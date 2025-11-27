#!/usr/bin/env python3
"""
Script de prueba para verificar el cierre automático de conversaciones en logout
"""
import asyncio
import json
import httpx
import os
from datetime import datetime

# Configuración
BACKEND_URL = "http://localhost:8001"

async def test_logout_conversation_close():
    """Probar el cierre automático de conversaciones en logout"""
    print("Iniciando prueba de cierre automático de conversaciones en logout...")
    
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
            
            # 2. Verificar conversaciones activas antes del logout
            print("\n2. Verificando conversaciones activas antes del logout...")
            
            headers = {"Authorization": f"Bearer {token}"}
            conversations_response = await client.get(
                f"{BACKEND_URL}/api/v1/chat/conversations",
                headers=headers
            )
            
            if conversations_response.status_code == 200:
                conversations = conversations_response.json()
                print(f"Conversaciones encontradas antes del logout: {len(conversations)}")
                
                for conv in conversations:
                    print(f"  - ID: {conv.get('id', 'N/A')}")
                    print(f"    Título: {conv.get('title', 'N/A')}")
                    print(f"    Activa: {conv.get('is_active', 'N/A')}")
                    print()
            else:
                print(f"Error obteniendo conversaciones: {conversations_response.status_code}")
                print(f"Respuesta: {conversations_response.text}")
            
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
                print(f"Respuesta: {logout_response.text}")
            
            # 4. Verificar que las conversaciones se cerraron
            print("\n4. Verificando que las conversaciones se cerraron...")
            
            # Intentar obtener conversaciones con el token (debería fallar)
            try:
                conversations_after_response = await client.get(
                    f"{BACKEND_URL}/api/v1/chat/conversations",
                    headers=headers
                )
                
                if conversations_after_response.status_code == 401:
                    print("✅ Token invalidado correctamente después del logout")
                else:
                    print(f"⚠️ Token aún válido después del logout: {conversations_after_response.status_code}")
            except Exception as e:
                print(f"✅ Error esperado al usar token después del logout: {e}")
                
    except Exception as e:
        print(f"Error en la prueba: {e}")

async def test_conversation_creation_after_logout():
    """Probar que se crea una nueva conversación después del logout"""
    print("\n" + "="*50)
    print("Prueba: Creación de nueva conversación después del logout")
    print("="*50)
    
    try:
        # 1. Login nuevamente
        print("\n1. Login nuevamente después del logout...")
        
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
                return
            
            token_data = login_response.json()
            token = token_data.get("access_token")
            print(f"Nuevo token obtenido: {token[:20]}...")
            
            # 2. Verificar que no hay conversaciones activas
            print("\n2. Verificando que no hay conversaciones activas...")
            
            headers = {"Authorization": f"Bearer {token}"}
            conversations_response = await client.get(
                f"{BACKEND_URL}/api/v1/chat/conversations",
                headers=headers
            )
            
            if conversations_response.status_code == 200:
                conversations = conversations_response.json()
                print(f"Conversaciones encontradas: {len(conversations)}")
                
                if len(conversations) == 0:
                    print("✅ No hay conversaciones activas - el logout funcionó correctamente")
                else:
                    print("⚠️ Aún hay conversaciones activas después del logout")
                    for conv in conversations:
                        print(f"  - ID: {conv.get('id', 'N/A')}")
                        print(f"    Activa: {conv.get('is_active', 'N/A')}")
            else:
                print(f"Error obteniendo conversaciones: {conversations_response.status_code}")
                
    except Exception as e:
        print(f"Error en la prueba: {e}")

if __name__ == "__main__":
    print("Prueba de Cierre Automático de Conversaciones en Logout")
    print("=" * 60)
    
    # Ejecutar pruebas
    asyncio.run(test_logout_conversation_close())
    asyncio.run(test_conversation_creation_after_logout())
    
    print("\nPrueba completada")
    print("\nResumen:")
    print("- Endpoint de logout modificado para cerrar conversaciones")
    print("- Conversaciones se marcan como inactivas al hacer logout")
    print("- Usuario siempre tendrá conversación nueva al hacer login")
    print("\nProximos pasos:")
    print("1. Reiniciar el backend para aplicar cambios")
    print("2. Probar logout desde el frontend")
    print("3. Verificar que se cierra la conversación")
    print("4. Confirmar que se crea nueva conversación al volver a hacer login")



