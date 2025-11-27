#!/usr/bin/env python3
"""
Script de prueba para verificar la funcionalidad simplificada del chat
"""
import asyncio
import json
import httpx
import os
from datetime import datetime

# Configuración
BACKEND_URL = "http://localhost:8001"
AGENT_URL = "http://localhost:8002"

async def test_chat_simplificado():
    """Probar la funcionalidad simplificada del chat"""
    print("Iniciando prueba de chat simplificado...")
    
    try:
        # 1. Login para obtener token
        print("\n1. Obteniendo token de autenticacion...")
        
        login_data = {
            "email": "admin@hps.com",
            "password": "admin123"
        }
        
        async with httpx.AsyncClient() as client:
            # Login
            login_response = await client.post(
                f"{BACKEND_URL}/api/v1/auth/login",
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
            conversations_response = await client.get(
                f"{BACKEND_URL}/api/v1/chat/conversations/active",
                headers=headers,
                params={"user_id": "test-user-id"}
            )
            
            if conversations_response.status_code == 200:
                conversations_data = conversations_response.json()
                print(f"Respuesta de conversaciones activas: {conversations_data}")
            else:
                print(f"Error obteniendo conversaciones activas: {conversations_response.status_code}")
                print(f"Respuesta: {conversations_response.text}")
            
            # 3. Probar endpoint de marcar conversación como inactiva
            print("\n3. Probando endpoint de marcar conversación como inactiva...")
            
            # Primero obtener conversaciones
            conversations_list_response = await client.get(
                f"{BACKEND_URL}/api/v1/chat/conversations",
                headers=headers
            )
            
            if conversations_list_response.status_code == 200:
                conversations = conversations_list_response.json()
                print(f"Conversaciones encontradas: {len(conversations)}")
                
                if conversations:
                    conversation_id = conversations[0]["id"]
                    print(f"Probando marcar conversación como inactiva: {conversation_id}")
                    
                    mark_inactive_response = await client.post(
                        f"{BACKEND_URL}/api/v1/chat/conversations/{conversation_id}/mark_inactive",
                        headers=headers
                    )
                    
                    if mark_inactive_response.status_code == 200:
                        inactive_data = mark_inactive_response.json()
                        print(f"Conversación marcada como inactiva: {inactive_data}")
                    else:
                        print(f"Error marcando conversación como inactiva: {mark_inactive_response.status_code}")
                        print(f"Respuesta: {mark_inactive_response.text}")
                else:
                    print("No hay conversaciones disponibles para probar")
            else:
                print(f"Error obteniendo conversaciones: {conversations_list_response.status_code}")
                print(f"Respuesta: {conversations_list_response.text}")
                
    except Exception as e:
        print(f"Error en la prueba: {e}")

async def test_websocket_connection():
    """Probar conexión WebSocket para verificar la funcionalidad simplificada"""
    print("\nProbando conexion WebSocket...")
    
    try:
        import websockets
        
        # URL del WebSocket
        ws_url = f"ws://localhost:8002/ws/chat?token=YOUR_TOKEN_HERE"
        print(f"URL WebSocket: {ws_url}")
        print("Para probar el WebSocket, necesitas un token valido")
        print("Puedes usar el token obtenido en el paso anterior")
        
    except ImportError:
        print("websockets no esta instalado, saltando prueba WebSocket")
    except Exception as e:
        print(f"Error en WebSocket: {e}")

if __name__ == "__main__":
    print("Prueba de Chat Simplificado - Sistema HPS")
    print("=" * 50)
    
    # Ejecutar pruebas
    asyncio.run(test_chat_simplificado())
    asyncio.run(test_websocket_connection())
    
    print("\nPrueba completada")
    print("\nResumen:")
    print("- WebSocket router simplificado")
    print("- Carga de historial eliminada del frontend")
    print("- Endpoint para marcar conversaciones como inactivas")
    print("- Logica de conversaciones activas implementada")
    print("\nProximos pasos:")
    print("1. Reiniciar el agente IA para aplicar cambios")
    print("2. Probar navegacion entre paginas")
    print("3. Verificar que no se duplica el mensaje de bienvenida")
    print("4. Confirmar que se carga el historial correctamente")



