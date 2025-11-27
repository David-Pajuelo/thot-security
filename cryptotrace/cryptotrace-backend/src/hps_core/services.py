from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import timedelta
from typing import Optional

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from .models import HpsRequest, HpsToken
from .tasks import send_hps_credentials_email
from .email_service import HpsEmailService

logger = logging.getLogger(__name__)
email_service = HpsEmailService()
User = get_user_model()


@dataclass
class TokenMetadata:
    email: str
    requested_by_id: int
    purpose: Optional[str] = None
    hours_valid: int = 72


class HpsTokenService:
    @staticmethod
    def create_token(meta: TokenMetadata) -> HpsToken:
        expires = timezone.now() + timedelta(hours=meta.hours_valid)
        token = HpsToken.objects.create(
            email=meta.email,
            requested_by_id=meta.requested_by_id,
            purpose=meta.purpose or "",
            expires_at=expires,
        )
        logger.info("Token HPS creado para %s expira %s", meta.email, expires)
        return token

    @staticmethod
    def mark_used(token: HpsToken):
        token.is_used = True
        token.used_at = timezone.now()
        token.save(update_fields=["is_used", "used_at"])


class HpsRequestService:
    @staticmethod
    @transaction.atomic
    def create_from_token(*, serializer, token: HpsToken, form_type: str):
        """
        Crear solicitud HPS desde un token público.
        
        El usuario se crea o busca basado en el email del token, no en token.requested_by.
        Si el usuario no existe, se crea automáticamente con un perfil HPS básico.
        """
        # Obtener el email del formulario o del token
        form_email = serializer.validated_data.get("email") or token.email
        
        # Buscar o crear el usuario basado en el email del token
        try:
            user = User.objects.get(email=form_email)
        except User.DoesNotExist:
            # Crear nuevo usuario si no existe
            # Usar email como username (Django requiere username único)
            username = form_email.split('@')[0]  # Parte antes del @
            # Asegurar que el username sea único
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            
            # Obtener nombre del formulario si está disponible
            first_name = serializer.validated_data.get("first_name", "")
            last_name = serializer.validated_data.get("first_last_name", "")
            
            user = User.objects.create_user(
                username=username,
                email=form_email,
                first_name=first_name,
                last_name=last_name,
                is_active=True,
            )
            logger.info(f"Usuario creado automáticamente para email: {form_email}")
        
        # Crear la solicitud HPS con el usuario correcto
        hps_request: HpsRequest = serializer.save(
            user=user,
            submitted_by=user,
            form_type=form_type,
        )
        HpsTokenService.mark_used(token)

        # Enviar email con credenciales si el email coincide
        if form_email == token.email:
            send_hps_credentials_email.delay(
                {
                    "to": token.email,
                    "request": str(hps_request.id),
                    "form_type": form_type,
                }
            )

        return hps_request

    @staticmethod
    def approve(hps_request: HpsRequest, user, expires_at=None, notes=""):
        old_status = hps_request.status
        hps_request.approve(user, expires_at)
        if notes:
            hps_request.notes = notes
        hps_request.save()
        
        # Enviar email de actualización de estado
        email_service.send_hps_status_update_email(
            hps_request, 
            new_status=hps_request.status,
            old_status=old_status
        )
        
        return hps_request

    @staticmethod
    def reject(hps_request: HpsRequest, user, notes=""):
        old_status = hps_request.status
        hps_request.reject(user, notes)
        hps_request.save()
        
        # Enviar email de actualización de estado
        email_service.send_hps_status_update_email(
            hps_request, 
            new_status=hps_request.status,
            old_status=old_status
        )
        
        return hps_request

