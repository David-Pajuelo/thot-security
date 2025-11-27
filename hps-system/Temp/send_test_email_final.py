#!/usr/bin/env python3
"""
Script simple para enviar un email de prueba usando requests
"""

import requests
import json
from datetime import datetime

# Configuración
API_BASE_URL = "http://localhost:8001"
TEST_EMAIL = "pajuelodev@gmail.com"

def send_test_email():
    """Envía un email de prueba usando la API"""
    
    print("Enviando email de prueba via API...")
    print(f"Destinatario: {TEST_EMAIL}")
    print(f"API URL: {API_BASE_URL}")
    
    # Datos del email de prueba
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
        # Enviar request a la API
        print("Enviando request a la API...")
        response = requests.post(
            f"{API_BASE_URL}/api/v1/email/send",
            json=email_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("EMAIL ENVIADO EXITOSAMENTE")
            print(f"Respuesta: {result}")
            print(f"Asunto: Confirmacion de solicitud HPS - 12345678A")
            print(f"Destinatario: {TEST_EMAIL}")
            print("\nRevisa tu bandeja de entrada en pajuelodev@gmail.com")
            return True
        else:
            print(f"Error en la API: {response.status_code}")
            print(f"Respuesta: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("Error: No se puede conectar a la API")
        print("Verificar que el backend este ejecutandose en http://localhost:8001")
        return False
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_api_connection():
    """Prueba la conexión a la API"""
    
    print("Probando conexion a la API...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/email/templates", timeout=10)
        if response.status_code == 200:
            print("API conectada exitosamente")
            return True
        else:
            print(f"API respondio con codigo: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("No se puede conectar a la API")
        print("Verificar que el backend este ejecutandose")
        return False
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("Sistema de Emails HPS - Prueba de Envio")
    print("=" * 50)
    
    # Probar conexión a la API
    if test_api_connection():
        # Enviar email de prueba
        success = send_test_email()
        
        if success:
            print("\nPRIMER EMAIL ENVIADO - Esperando confirmacion...")
            print("Busca el email con asunto: 'Confirmacion de solicitud HPS - 12345678A'")
        else:
            print("\nError enviando email")
    else:
        print("\nNo se puede continuar sin conexion a la API")



