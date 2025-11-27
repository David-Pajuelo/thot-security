#!/usr/bin/env python3
"""
Script de prueba para verificar el flujo de conversaciones del chat
"""
import asyncio
import httpx
import json
import time

async def test_chat_conversation_flow():
    """Probar el flujo completo de conversaciones del chat"""
    print("Probando flujo de conversaciones del chat...")
    
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
            
            # 2. Verificar conversaciones antes del logout
            print("\n2. Verificando conversaciones antes del logout...")
            
            headers = {"Authorization": f"Bearer {token}"}
            
            # Obtener conversaciones del usuario
            conversations_response = await client.get(
                "http://localhost:8001/api/v1/chat/conversations",
                headers=headers
            )
            
            if conversations_response.status_code == 200:
                conversations = conversations_response.json()
                print(f"Conversaciones encontradas: {len(conversations)}")
                
                for conv in conversations:
                    print(f"  - ID: {conv.get('id', 'N/A')}")
                    print(f"    Título: {conv.get('title', 'N/A')}")
                    print(f"    Estado: {conv.get('status', 'N/A')}")
                    print(f"    Creada: {conv.get('created_at', 'N/A')}")
                    print(f"    Cerrada: {conv.get('closed_at', 'N/A')}")
                    print()
            else:
                print(f"Error obteniendo conversaciones: {conversations_response.status_code}")
            
            # 3. Probar endpoint de conversaciones activas
            print("\n3. Probando endpoint de conversaciones activas...")
            
            # Usar el ID del usuario actual
            user_id = "admin"  # Intentar con este ID primero
            
            active_response = await client.get(
                f"http://localhost:8001/api/v1/chat/conversations/active",
                headers=headers,
                params={"user_id": user_id}
            )
            
            print(f"Status code: {active_response.status_code}")
            print(f"Respuesta: {active_response.text}")
            
            if active_response.status_code == 200:
                data = active_response.json()
                print(f"Conversación activa: {data.get('conversation_id', 'N/A')}")
            else:
                print(f"Error: {active_response.status_code}")
            
            # 4. Hacer logout
            print("\n4. Haciendo logout...")
            
            logout_response = await client.post(
                "http://localhost:8001/api/v1/auth/logout",
                headers=headers
            )
            
            if logout_response.status_code == 200:
                logout_data = logout_response.json()
                print(f"Logout exitoso: {logout_data.get('message', 'N/A')}")
                print(f"Detalle: {logout_data.get('detail', 'N/A')}")
            else:
                print(f"Error en logout: {logout_response.status_code}")
            
            # 5. Verificar conversaciones después del logout
            print("\n5. Verificando conversaciones después del logout...")
            
            # Login nuevamente para verificar
            login_response2 = await client.post(
                "http://localhost:8001/api/v1/auth/login",
                json=login_data
            )
            
            if login_response2.status_code == 200:
                token_data2 = login_response2.json()
                token2 = token_data2.get("access_token")
                headers2 = {"Authorization": f"Bearer {token2}"}
                
                conversations_after_response = await client.get(
                    "http://localhost:8001/api/v1/chat/conversations",
                    headers=headers2
                )
                
                if conversations_after_response.status_code == 200:
                    conversations_after = conversations_after_response.json()
                    print(f"Conversaciones después del logout: {len(conversations_after)}")
                    
                    for conv in conversations_after:
                        print(f"  - ID: {conv.get('id', 'N/A')}")
                        print(f"    Título: {conv.get('title', 'N/A')}")
                        print(f"    Estado: {conv.get('status', 'N/A')}")
                        print(f"    Creada: {conv.get('created_at', 'N/A')}")
                        print(f"    Cerrada: {conv.get('closed_at', 'N/A')}")
                        print()
                else:
                    print(f"Error obteniendo conversaciones después del logout: {conversations_after_response.status_code}")
            else:
                print(f"Error en segundo login: {login_response2.status_code}")
                
    except Exception as e:
        print(f"Error en la prueba: {e}")

if __name__ == "__main__":
    print("Prueba de Flujo de Conversaciones del Chat")
    print("=" * 60)
    
    asyncio.run(test_chat_conversation_flow())
    
    print("\nPrueba completada")
    print("\nResumen:")
    print("- Verificar que el endpoint de conversaciones activas funciona")
    print("- Verificar que el logout cierra la conversación")
    print("- Verificar que se crea nueva conversación al hacer login")
    print("\nProximos pasos:")
    print("1. Probar desde el frontend")
    print("2. Verificar que no se muestra mensaje de bienvenida duplicado")
    print("3. Confirmar que se cierra la conversación al hacer logout")



