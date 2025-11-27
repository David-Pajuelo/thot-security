#!/usr/bin/env python3
"""
Script para eliminar el historial del chat
"""
import sys
import os

# Agregar el directorio del proyecto al path
sys.path.append('/app')

from src.database.database import SessionLocal
from src.models.chat_conversation import ChatConversation
from src.models.chat_message import ChatMessage

def eliminar_historial():
    """Eliminar todo el historial del chat"""
    db = SessionLocal()
    try:
        # Verificar conversaciones existentes
        conversations = db.query(ChatConversation).all()
        print(f'📊 Conversaciones encontradas: {len(conversations)}')
        
        for conv in conversations:
            print(f'  - ID: {conv.id}')
            print(f'    Usuario: {conv.user_id}')
            print(f'    Título: {conv.title}')
            print(f'    Activa: {conv.is_active}')
            print(f'    Creada: {conv.created_at}')
            print()
        
        # Verificar mensajes
        messages = db.query(ChatMessage).all()
        print(f'📊 Mensajes encontrados: {len(messages)}')
        
        if conversations or messages:
            print('🧹 Eliminando historial...')
            
            # Eliminar todos los mensajes
            db.query(ChatMessage).delete()
            print('✅ Todos los mensajes eliminados')
            
            # Eliminar todas las conversaciones
            db.query(ChatConversation).delete()
            print('✅ Todas las conversaciones eliminadas')
            
            # Confirmar cambios
            db.commit()
            print('✅ Historial eliminado exitosamente')
        else:
            print('ℹ️ No hay historial para eliminar')
            
    except Exception as e:
        print(f'❌ Error: {e}')
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    eliminar_historial()
