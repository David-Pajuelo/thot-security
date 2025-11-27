#!/usr/bin/env python3
"""
Script para probar el envío real de emails usando el sistema del backend
"""

import sys
import os
import requests
import json
from datetime import datetime

# Configuración
API_BASE_URL = "http://localhost:8001"
TEST_EMAIL = "pajuelodev@gmail.com"

def get_auth_token():
    """Obtiene token de autenticación"""
    
    print("Obteniendo token de autenticacion...")
    
    # Datos de login (usar credenciales de admin)
    login_data = {
        "email": "admin@hps.com",
        "password": "admin123"
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            token = result.get("access_token")
            print("Token obtenido exitosamente")
            return token
        else:
            print(f"Error en login: {response.status_code}")
            print(f"Respuesta: {response.text}")
            return None
            
    except Exception as e:
        print(f"Error obteniendo token: {str(e)}")
        return None

def send_confirmation_email(token):
    """Envía email de confirmación usando la API"""
    
    print("Enviando email de confirmacion...")
    
    # Datos del email
    email_data = {
        "to": TEST_EMAIL,
        "template": "confirmation",
        "template_data": {
            "user_name": "Juan Perez Garcia",
            "user_email": TEST_EMAIL,
            "document_number": "12345678A",
            "request_type": "nueva",
            "status": "pending",
            "hps_request_id": 1,
            "additional_data": {
                "request_date": datetime.now().strftime("%d/%m/%Y %H:%M")
            }
        }
    }
    
    try:
        # Enviar request con autenticación
        response = requests.post(
            f"{API_BASE_URL}/api/v1/email/send",
            json=email_data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("EMAIL ENVIADO EXITOSAMENTE")
            print(f"Respuesta: {result}")
            return True
        else:
            print(f"Error enviando email: {response.status_code}")
            print(f"Respuesta: {response.text}")
            return False
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def send_status_update_email(token):
    """Envía email de actualización de estado"""
    
    print("Enviando email de actualizacion de estado...")
    
    # Datos del email
    email_data = {
        "to": TEST_EMAIL,
        "template": "status_update",
        "template_data": {
            "user_name": "Maria Garcia Lopez",
            "user_email": TEST_EMAIL,
            "document_number": "87654321B",
            "request_type": "renovacion",
            "status": "approved",
            "hps_request_id": 2,
            "additional_data": {
                "old_status": "pending",
                "new_status": "approved"
            }
        }
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/email/send",
            json=email_data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("EMAIL DE ACTUALIZACION ENVIADO EXITOSAMENTE")
            print(f"Respuesta: {result}")
            return True
        else:
            print(f"Error enviando email: {response.status_code}")
            print(f"Respuesta: {response.text}")
            return False
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def send_reminder_email(token):
    """Envía email de recordatorio"""
    
    print("Enviando email de recordatorio...")
    
    # Datos del email
    email_data = {
        "to": TEST_EMAIL,
        "template": "reminder",
        "template_data": {
            "user_name": "Carlos Alonso Ruiz",
            "user_email": TEST_EMAIL,
            "document_number": "11223344C",
            "request_type": "nueva",
            "status": "pending",
            "hps_request_id": 3,
            "additional_data": {
                "request_date": "05/10/2025 10:30",
                "days_pending": "4"
            }
        }
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/email/send",
            json=email_data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("EMAIL DE RECORDATORIO ENVIADO EXITOSAMENTE")
            print(f"Respuesta: {result}")
            return True
        else:
            print(f"Error enviando email: {response.status_code}")
            print(f"Respuesta: {response.text}")
            return False
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def send_new_user_notification_email(token):
    """Envía email de notificación de nuevo usuario"""
    
    print("Enviando email de notificacion de nuevo usuario...")
    
    # Datos del email
    email_data = {
        "to": TEST_EMAIL,
        "template": "new_user_notification",
        "template_data": {
            "user_name": "Ana Martinez Sanchez",
            "user_email": "ana.martinez@empresa.com",
            "recipient_name": "Angel Bonacasa",
            "recipient_email": TEST_EMAIL,
            "additional_data": {
                "user_role": "member",
                "team_name": "Equipo AICOX",
                "registration_date": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "created_by": "Carlos Alonso",
                "recipient_role": "jefe_seguridad"
            }
        }
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/email/send",
            json=email_data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("EMAIL DE NOTIFICACION ENVIADO EXITOSAMENTE")
            print(f"Respuesta: {result}")
            return True
        else:
            print(f"Error enviando email: {response.status_code}")
            print(f"Respuesta: {response.text}")
            return False
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("Sistema de Emails HPS - Prueba Real")
    print("=" * 50)
    print(f"Destinatario: {TEST_EMAIL}")
    print("=" * 50)
    
    # Obtener token de autenticación
    token = get_auth_token()
    
    if not token:
        print("No se puede continuar sin token de autenticacion")
        exit(1)
    
    # Enviar primer email (confirmación)
    print("\n1. Enviando email de confirmacion...")
    success1 = send_confirmation_email(token)
    
    if success1:
        print("\nPRIMER EMAIL ENVIADO EXITOSAMENTE")
        print("Revisa tu bandeja de entrada en pajuelodev@gmail.com")
        print("Busca el email con asunto: 'Confirmacion de solicitud HPS - 12345678A'")
        
        # Esperar confirmación
        input("\nPresiona Enter cuando hayas confirmado que llego el primer email...")
        
        # Continuar con el resto
        print("\nContinuando con el resto de emails...")
        
        # Email 2: Actualización de estado
        print("\n2. Enviando email de actualizacion de estado...")
        success2 = send_status_update_email(token)
        
        # Email 3: Recordatorio
        print("\n3. Enviando email de recordatorio...")
        success3 = send_reminder_email(token)
        
        # Email 4: Notificación de nuevo usuario
        print("\n4. Enviando email de notificacion de nuevo usuario...")
        success4 = send_new_user_notification_email(token)
        
        # Resumen
        print("\n" + "=" * 50)
        print("RESUMEN DE ENVIOS")
        print("=" * 50)
        print(f"Confirmacion: {'OK' if success1 else 'ERROR'}")
        print(f"Actualizacion: {'OK' if success2 else 'ERROR'}")
        print(f"Recordatorio: {'OK' if success3 else 'ERROR'}")
        print(f"Notificacion: {'OK' if success4 else 'ERROR'}")
        
        total_success = sum([success1, success2, success3, success4])
        print(f"\nTotal exitosos: {total_success}/4")
        
        if total_success == 4:
            print("TODOS LOS EMAILS ENVIADOS EXITOSAMENTE")
        else:
            print("Algunos emails fallaron")
    else:
        print("Error enviando el primer email")



