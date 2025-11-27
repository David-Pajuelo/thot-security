#!/usr/bin/env python3
"""
Script de prueba para el botón Reset Chat
"""
import asyncio
import httpx
import json

async def test_reset_chat():
    """Probar el endpoint de reset chat"""
    print("Probando endpoint de reset chat...")
    
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
            
            # 2. Verificar conversaciones antes del reset
            print("\n2. Verificando conversaciones antes del reset...")
            
            headers = {"Authorization": f"Bearer {token}"}
            
            conversations_response = await client.get(
                "http://localhost:8001/api/v1/chat/conversations",
                headers=headers
            )
            
            if conversations_response.status_code == 200:
                conversations = conversations_response.json()
                print(f"Conversaciones encontradas: {len(conversations)}")
                
                for i, conv in enumerate(conversations):
                    print(f"  {i+1}. ID: {conv.get('id', 'N/A')}")
                    print(f"     Título: {conv.get('title', 'N/A')}")
                    print(f"     Estado: {conv.get('status', 'N/A')}")
                    print(f"     Creada: {conv.get('created_at', 'N/A')}")
                    print(f"     Cerrada: {conv.get('closed_at', 'N/A')}")
                    print()
            else:
                print(f"Error obteniendo conversaciones: {conversations_response.status_code}")
            
            # 3. Probar endpoint de reset
            print("\n3. Probando endpoint de reset...")
            
            reset_response = await client.post(
                "http://localhost:8001/api/v1/chat/conversations/reset",
                headers=headers
            )
            
            print(f"Status code: {reset_response.status_code}")
            print(f"Respuesta: {reset_response.text}")
            
            if reset_response.status_code == 200:
                data = reset_response.json()
                print(f"Reset exitoso:")
                print(f"  - Mensaje: {data.get('message', 'N/A')}")
                print(f"  - Nueva conversación: {data.get('new_conversation_id', 'N/A')}")
                print(f"  - Conversación archivada: {data.get('archived_conversation_id', 'N/A')}")
            else:
                print(f"Error en reset: {reset_response.status_code}")
            
            # 4. Verificar conversaciones después del reset
            print("\n4. Verificando conversaciones después del reset...")
            
            conversations_after_response = await client.get(
                "http://localhost:8001/api/v1/chat/conversations",
                headers=headers
            )
            
            if conversations_after_response.status_code == 200:
                conversations_after = conversations_after_response.json()
                print(f"Conversaciones después del reset: {len(conversations_after)}")
                
                for i, conv in enumerate(conversations_after):
                    print(f"  {i+1}. ID: {conv.get('id', 'N/A')}")
                    print(f"     Título: {conv.get('title', 'N/A')}")
                    print(f"     Estado: {conv.get('status', 'N/A')}")
                    print(f"     Creada: {conv.get('created_at', 'N/A')}")
                    print(f"     Cerrada: {conv.get('closed_at', 'N/A')}")
                    print()
            else:
                print(f"Error obteniendo conversaciones después del reset: {conversations_after_response.status_code}")
                
    except Exception as e:
        print(f"Error en la prueba: {e}")

if __name__ == "__main__":
    print("Prueba del Botón Reset Chat")
    print("=" * 60)
    
    asyncio.run(test_reset_chat())
    
    print("\nPrueba completada")
    print("\nResumen:")
    print("- Endpoint de reset implementado")
    print("- Botón Reset agregado al frontend")
    print("- Función handleResetChat implementada")
    print("\nProximos pasos:")
    print("1. Probar desde el frontend")
    print("2. Verificar que se archiva la conversación actual")
    print("3. Confirmar que se crea nueva conversación")
    print("4. Verificar que se muestra mensaje de bienvenida")



