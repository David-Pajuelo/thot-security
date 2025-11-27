#!/usr/bin/env python3
"""
Script de prueba para verificar el endpoint de conversaciones activas
"""
import asyncio
import httpx
import json

async def test_active_conversation():
    """Probar el endpoint de conversaciones activas"""
    print("Probando endpoint de conversaciones activas...")
    
    try:
        # 1. Login para obtener token
        print("\n1. Login...")
        
        login_data = {
            "email": "admin@hps.com",
            "password": "admin123"
        }
        
        async with httpx.AsyncClient() as client:
            login_response = await client.post(
                "http://localhost:8001/api/v1/auth/login",
                json=login_data
            )
            
            if login_response.status_code != 200:
                print(f"Error en login: {login_response.status_code}")
                print(f"Respuesta: {login_response.text}")
                return
            
            token_data = login_response.json()
            token = token_data.get("access_token")
            print(f"Token obtenido: {token[:20]}...")
            
            # 2. Probar endpoint de conversaciones activas
            print("\n2. Probando endpoint de conversaciones activas...")
            
            headers = {"Authorization": f"Bearer {token}"}
            
            # Usar el ID del usuario admin (necesitamos obtenerlo)
            user_id = "admin"  # Intentar con este ID primero
            
            response = await client.get(
                f"http://localhost:8001/api/v1/chat/conversations/active",
                headers=headers,
                params={"user_id": user_id}
            )
            
            print(f"Status code: {response.status_code}")
            print(f"Respuesta: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Conversación activa: {data.get('conversation_id', 'N/A')}")
            else:
                print(f"Error: {response.status_code}")
                
    except Exception as e:
        print(f"Error en la prueba: {e}")

if __name__ == "__main__":
    asyncio.run(test_active_conversation())



