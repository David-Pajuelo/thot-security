#!/usr/bin/env python3
"""
Script para consultar datos del usuario 5432343U
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from src.database.database import get_db
from src.models.hps import HPSRequest
from src.models.user import User
from sqlalchemy.orm import joinedload

def consultar_usuario():
    db = next(get_db())
    
    print("=== CONSULTA USUARIO 5432343U ===\n")
    
    # Buscar solicitudes HPS por número de documento
    hps_requests = db.query(HPSRequest).filter(
        HPSRequest.document_number == '5432343U'
    ).options(
        joinedload(HPSRequest.user),
        joinedload(HPSRequest.submitted_by_user),
        joinedload(HPSRequest.approved_by_user)
    ).all()
    
    if not hps_requests:
        print("❌ No se encontraron solicitudes HPS para el documento 5432343U")
        return
    
    print(f"✅ Se encontraron {len(hps_requests)} solicitud(es) HPS:\n")
    
    for i, hps in enumerate(hps_requests, 1):
        print(f"--- SOLICITUD {i} ---")
        print(f"ID: {hps.id}")
        print(f"Tipo de documento: {hps.document_type}")
        print(f"Número de documento: {hps.document_number}")
        print(f"Nombre completo: {hps.first_name} {hps.first_last_name} {hps.second_last_name or ''}")
        print(f"Fecha de nacimiento: {hps.birth_date}")
        print(f"Nacionalidad: {hps.nationality}")
        print(f"Lugar de nacimiento: {hps.birth_place}")
        print(f"Email: {hps.email}")
        print(f"Teléfono: {hps.phone}")
        print(f"Tipo de solicitud: {hps.request_type}")
        print(f"Tipo HPS: {hps.type}")
        print(f"Estado: {hps.status}")
        print(f"Fecha de solicitud: {hps.submitted_at}")
        print(f"Fecha de aprobación: {hps.approved_at}")
        print(f"Fecha de expiración: {hps.expires_at}")
        print(f"Notas: {hps.notes}")
        print(f"Grado de habilitación: {hps.security_clearance_level}")
        print(f"Expediente gobierno: {hps.government_expediente}")
        print(f"Empresa: {hps.company_name}")
        
        # Información del usuario asociado
        if hps.user:
            print(f"\n--- USUARIO ASOCIADO ---")
            print(f"User ID: {hps.user.id}")
            print(f"Email usuario: {hps.user.email}")
            print(f"Nombre usuario: {hps.user.first_name} {hps.user.last_name}")
            print(f"Rol: {hps.user.role.name if hps.user.role else 'N/A'}")
            print(f"Equipo: {hps.user.team.name if hps.user.team else 'N/A'}")
            print(f"Activo: {hps.user.is_active}")
            print(f"Email verificado: {hps.user.email_verified}")
            print(f"Último login: {hps.user.last_login}")
        
        # Información de quién envió la solicitud
        if hps.submitted_by_user:
            print(f"\n--- ENVIADO POR ---")
            print(f"Nombre: {hps.submitted_by_user.first_name} {hps.submitted_by_user.last_name}")
            print(f"Email: {hps.submitted_by_user.email}")
            print(f"Rol: {hps.submitted_by_user.role.name if hps.submitted_by_user.role else 'N/A'}")
        
        # Información de quién aprobó la solicitud
        if hps.approved_by_user:
            print(f"\n--- APROBADO POR ---")
            print(f"Nombre: {hps.approved_by_user.first_name} {hps.approved_by_user.last_name}")
            print(f"Email: {hps.approved_by_user.email}")
            print(f"Rol: {hps.approved_by_user.role.name if hps.approved_by_user.role else 'N/A'}")
        
        print("\n" + "="*50 + "\n")
    
    # Buscar también por email por si acaso
    print("--- BÚSQUEDA ADICIONAL POR EMAIL ---")
    if hps_requests:
        email = hps_requests[0].email
        print(f"Buscando usuario con email: {email}")
        
        user = db.query(User).filter(User.email == email).first()
        if user:
            print(f"✅ Usuario encontrado en tabla users:")
            print(f"   ID: {user.id}")
            print(f"   Email: {user.email}")
            print(f"   Nombre: {user.first_name} {user.last_name}")
            print(f"   Rol: {user.role.name if user.role else 'N/A'}")
            print(f"   Equipo: {user.team.name if user.team else 'N/A'}")
            print(f"   Activo: {user.is_active}")
            print(f"   Email verificado: {user.email_verified}")
        else:
            print("❌ No se encontró usuario en tabla users con ese email")

if __name__ == "__main__":
    consultar_usuario()
