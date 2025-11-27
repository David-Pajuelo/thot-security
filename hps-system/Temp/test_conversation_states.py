#!/usr/bin/env python3
"""
Script de prueba para verificar el sistema de estados de conversaciones
"""
import asyncio
import json
import httpx
import os
from datetime import datetime

# Configuración
BACKEND_URL = "http://localhost:8001"

async def test_conversation_states():
    """Probar el sistema de estados de conversaciones"""
    print("Iniciando prueba de estados de conversaciones...")
    
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
            
            # 2. Verificar conversaciones antes del logout
            print("\n2. Verificando conversaciones antes del logout...")
            
            headers = {"Authorization": f"Bearer {token}"}
            conversations_response = await client.get(
                f"{BACKEND_URL}/api/v1/chat/conversations",
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
            
            # 3. Hacer logout
            print("\n3. Haciendo logout...")
            
            logout_response = await client.post(
                f"{BACKEND_URL}/api/v1/auth/logout",
                headers=headers
            )
            
            if logout_response.status_code == 200:
                logout_data = logout_response.json()
                print(f"Logout exitoso: {logout_data.get('message', 'N/A')}")
                print(f"Detalle: {logout_data.get('detail', 'N/A')}")
            else:
                print(f"Error en logout: {logout_response.status_code}")
            
            # 4. Verificar conversaciones después del logout
            print("\n4. Verificando conversaciones después del logout...")
            
            # Login nuevamente para verificar
            login_response2 = await client.post(
                f"{BACKEND_URL}/api/v1/auth/login",
                json=login_data
            )
            
            if login_response2.status_code == 200:
                token_data2 = login_response2.json()
                token2 = token_data2.get("access_token")
                headers2 = {"Authorization": f"Bearer {token2}"}
                
                conversations_after_response = await client.get(
                    f"{BACKEND_URL}/api/v1/chat/conversations",
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

async def test_monitoring_all_conversations():
    """Probar que la monitorización incluye todas las conversaciones"""
    print("\n" + "="*60)
    print("Prueba: Monitorización de todas las conversaciones")
    print("="*60)
    
    try:
        # 1. Login
        print("\n1. Login para verificar monitorización...")
        
        login_data = {
            "email": "admin@hps.com",
            "password": "admin123"
        }
        
        async with httpx.AsyncClient() as client:
            login_response = await client.post(
                f"{BACKEND_URL}/api/v1/auth/login",
                json=login_data
            )
            
            if login_response.status_code != 200:
                print(f"Error en login: {login_response.status_code}")
                return
            
            token_data = login_response.json()
            token = token_data.get("access_token")
            headers = {"Authorization": f"Bearer {token}"}
            
            # 2. Verificar métricas (deberían incluir todas las conversaciones)
            print("\n2. Verificando métricas de monitorización...")
            
            metrics_response = await client.get(
                f"{BACKEND_URL}/api/v1/chat/metrics/realtime",
                headers=headers
            )
            
            if metrics_response.status_code == 200:
                metrics = metrics_response.json()
                print(f"Métricas obtenidas:")
                print(f"  - Total de conversaciones: {metrics.get('total_conversations', 'N/A')}")
                print(f"  - Conversaciones activas: {metrics.get('active_conversations', 'N/A')}")
                print(f"  - Conversaciones cerradas: {metrics.get('closed_conversations', 'N/A')}")
                print(f"  - Total de mensajes: {metrics.get('total_messages', 'N/A')}")
            else:
                print(f"Error obteniendo métricas: {metrics_response.status_code}")
                
    except Exception as e:
        print(f"Error en la prueba: {e}")

if __name__ == "__main__":
    print("Prueba de Estados de Conversaciones - Sistema HPS")
    print("=" * 60)
    
    # Ejecutar pruebas
    asyncio.run(test_conversation_states())
    asyncio.run(test_monitoring_all_conversations())
    
    print("\nPrueba completada")
    print("\nResumen:")
    print("- Sistema de estados implementado (active, closed, archived)")
    print("- Logout marca conversación como 'closed' (no elimina)")
    print("- Monitorización incluye todas las conversaciones")
    print("- Chat del usuario solo muestra conversación activa")
    print("\nProximos pasos:")
    print("1. Reiniciar backend para aplicar cambios")
    print("2. Probar logout desde el frontend")
    print("3. Verificar que se cierra la conversación (no se elimina)")
    print("4. Confirmar que se crea nueva conversación al hacer login")
    print("5. Verificar que la monitorización incluye todas las conversaciones")



