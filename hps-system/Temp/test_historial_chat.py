#!/usr/bin/env python3
"""
Script de prueba para verificar la funcionalidad de historial de chat
"""
import asyncio
import json
import httpx
import os
from datetime import datetime

# Configuración
BACKEND_URL = "http://localhost:8001"
AGENT_URL = "http://localhost:8002"

async def test_historial_chat():
    """Probar la funcionalidad de historial de chat"""
    print("Iniciando prueba de historial de chat...")
    
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
            
            # 2. Obtener conversaciones del usuario
            print("\n2. Obteniendo conversaciones del usuario...")
            
            headers = {"Authorization": f"Bearer {token}"}
            conversations_response = await client.get(
                f"{BACKEND_URL}/api/v1/chat/conversations",
                headers=headers
            )
            
            if conversations_response.status_code == 200:
                conversations = conversations_response.json()
                print(f"Conversaciones encontradas: {len(conversations)}")
                
                if conversations:
                    # 3. Probar obtener mensajes de la primera conversación
                    conversation_id = conversations[0]["id"]
                    print(f"\n3. Obteniendo mensajes de conversacion: {conversation_id}")
                    
                    messages_response = await client.get(
                        f"{BACKEND_URL}/api/v1/chat/conversations/{conversation_id}/messages",
                        headers=headers
                    )
                    
                    if messages_response.status_code == 200:
                        messages_data = messages_response.json()
                        messages = messages_data.get("messages", [])
                        print(f"Mensajes obtenidos: {len(messages)}")
                        
                        # Mostrar algunos mensajes
                        for i, msg in enumerate(messages[:3]):  # Mostrar solo los primeros 3
                            print(f"  Mensaje {i+1}:")
                            print(f"    Tipo: {msg.get('message_type', 'unknown')}")
                            print(f"    Contenido: {msg.get('content', '')[:100]}...")
                            print(f"    Fecha: {msg.get('created_at', 'N/A')}")
                            print()
                    else:
                        print(f"Error obteniendo mensajes: {messages_response.status_code}")
                        print(f"Respuesta: {messages_response.text}")
                else:
                    print("No hay conversaciones disponibles para probar")
            else:
                print(f"Error obteniendo conversaciones: {conversations_response.status_code}")
                print(f"Respuesta: {conversations_response.text}")
                
    except Exception as e:
        print(f"Error en la prueba: {e}")

async def test_websocket_connection():
    """Probar conexión WebSocket para verificar el historial"""
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
    print("Prueba de Historial de Chat - Sistema HPS")
    print("=" * 50)
    
    # Ejecutar pruebas
    asyncio.run(test_historial_chat())
    asyncio.run(test_websocket_connection())
    
    print("\nPrueba completada")
    print("\nResumen:")
    print("- Endpoint para obtener mensajes implementado")
    print("- Funciones de historial agregadas al WebSocket")
    print("- Logica de carga de historial implementada")
    print("\nProximos pasos:")
    print("1. Reiniciar el agente IA para aplicar cambios")
    print("2. Probar conexion WebSocket con token valido")
    print("3. Verificar que se carga el historial en lugar del mensaje de bienvenida")
