#!/usr/bin/env python3
"""
Script simple para probar el endpoint de reset
"""
import requests
import json

def test_reset_endpoint():
    """Probar el endpoint de reset directamente"""
    print("Probando endpoint de reset...")
    
    try:
        # URL del endpoint
        url = "http://localhost:8001/api/v1/chat/conversations/reset"
        
        # Headers (necesitamos un token válido)
        headers = {
            "Content-Type": "application/json"
        }
        
        print(f"URL: {url}")
        print(f"Headers: {headers}")
        
        # Hacer la petición
        response = requests.post(url, headers=headers)
        
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Endpoint funcionando correctamente")
        else:
            print(f"❌ Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_reset_endpoint()



