#!/usr/bin/env python3
"""
Prueba final de notificaciones de nuevo usuario
"""

import requests

def test_notifications():
    print("Probando notificaciones de nuevo usuario...")
    
    # Login como admin
    login_data = {
        "email": "admin@hps-system.com",
        "password": "admin123"
    }
    
    login_response = requests.post("http://localhost:8001/api/v1/auth/login", json=login_data)
    if login_response.status_code != 200:
        print(f"Error en login: {login_response.status_code}")
        return
    
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Crear token HPS
    token_data = {
        "email": "testuser_notifications@example.com",
        "hps_type": "nueva"
    }
    
    token_response = requests.post("http://localhost:8001/api/v1/hps/tokens/", json=token_data, headers=headers)
    if token_response.status_code != 201:
        print(f"Error creando token: {token_response.status_code}")
        return
    
    hps_token = token_response.json()["token"]
    print(f"Token creado: {hps_token[:20]}...")
    
    # Enviar formulario HPS
    form_data = {
        "request_type": "new",
        "document_type": "DNI / NIF",
        "document_number": "88888888X",
        "birth_date": "1990-01-01",
        "first_name": "Test",
        "first_last_name": "User",
        "second_last_name": "Notifications",
        "nationality": "ESPAÑA",
        "birth_place": "Madrid",
        "email": "testuser_notifications@example.com",
        "phone": "600888888"
    }
    
    form_response = requests.post(
        f"http://localhost:8001/api/v1/hps/public?token={hps_token}&hps_type=nueva",
        json=form_data
    )
    
    if form_response.status_code != 200:
        print(f"Error enviando formulario: {form_response.status_code}")
        return
    
    print("Formulario enviado correctamente")
    print("Revisa los logs del backend para ver las notificaciones")

if __name__ == "__main__":
    test_notifications()
