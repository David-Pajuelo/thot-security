# 🔧 Solución: Mostrar Historial en lugar de Mensaje de Bienvenida

## 🎯 **Problema Identificado**

El mensaje de bienvenida solo se envía cuando se crea una **nueva conversación**, pero si ya existe una conversación activa, se reutiliza y **no se envía el mensaje de bienvenida**.

## 💡 **Solución Propuesta**

En lugar de enviar siempre el mensaje de bienvenida, **cargar y mostrar el historial de la conversación existente** cuando se reutiliza una conversación activa.

### **Lógica de la Solución:**
1. **Nueva conversación** → Enviar mensaje de bienvenida
2. **Conversación existente** → Cargar y mostrar historial de mensajes

## 🔧 **Implementación**

### **1. Modificar WebSocket Router**

#### **Archivo**: `agente-ia/src/websocket/router.py`
#### **Líneas**: 92-105

```python
# Si no hay conversación activa, crear una nueva
if not conversation_id:
    conversation_id = await chat_integration.start_conversation(
        user_id=user_id,
        session_id=session_id,
        title="Nueva conversación iniciada",
        auth_token=token
    )
    logger.info(f"✅ Nueva conversación creada: {conversation_id}")
    
    # Enviar mensaje de bienvenida para nueva conversación
    await send_welcome_message(websocket, user)
else:
    logger.info(f"✅ Reutilizando conversación activa: {conversation_id}")
    
    # ✅ NUEVA FUNCIONALIDAD: Cargar historial de conversación existente
    await send_conversation_history(websocket, conversation_id, user, token)
```

### **2. Crear Función para Cargar Historial**

#### **Nueva función en `agente-ia/src/websocket/router.py`:**

```python
async def send_conversation_history(websocket: WebSocket, conversation_id: str, user: dict, token: str):
    """Cargar y enviar historial de conversación existente"""
    try:
        # Obtener historial de mensajes de la conversación
        messages = await get_conversation_messages(conversation_id, token)
        
        if messages:
            logger.info(f"📜 Cargando {len(messages)} mensajes del historial")
            
            # Enviar cada mensaje del historial
            for message in messages:
                await websocket.send_text(json.dumps({
                    "type": message.get("message_type", "assistant"),
                    "message": message.get("content", ""),
                    "timestamp": message.get("created_at", datetime.now().isoformat()),
                    "suggestions": message.get("suggestions", [])
                }))
            
            logger.info(f"✅ Historial cargado exitosamente")
        else:
            # Si no hay historial, enviar mensaje de bienvenida
            await send_welcome_message(websocket, user)
            
    except Exception as e:
        logger.error(f"❌ Error cargando historial: {e}")
        # En caso de error, enviar mensaje de bienvenida
        await send_welcome_message(websocket, user)

async def get_conversation_messages(conversation_id: str, token: str) -> list:
    """Obtener mensajes de una conversación desde el backend"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        url = f"{os.getenv('BACKEND_URL', 'http://backend:8001')}/api/v1/chat/conversations/{conversation_id}/messages"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=10.0)
            
            if response.status_code == 200:
                data = response.json()
                return data.get("messages", [])
            else:
                logger.warning(f"⚠️ Error obteniendo mensajes: {response.status_code}")
                return []
                
    except Exception as e:
        logger.error(f"❌ Error obteniendo mensajes: {e}")
        return []
```

### **3. Crear Endpoint para Obtener Mensajes**

#### **Archivo**: `backend/src/chat/router.py`
#### **Nuevo endpoint**:

```python
@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: str,
    limit: int = Query(50, ge=1, le=100, description="Número máximo de mensajes"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener mensajes de una conversación específica"""
    try:
        # Verificar que la conversación existe
        conversation = ChatLoggingService.get_conversation_by_id(db, conversation_id)
        
        if not conversation:
            raise HTTPException(
                status_code=404,
                detail="Conversación no encontrada"
            )
        
        # Verificar permisos (solo admin o el propio usuario)
        if current_user.role.name != "admin" and conversation.user_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="No tienes permisos para ver esta conversación"
            )
        
        # Obtener mensajes de la conversación
        messages = ChatLoggingService.get_conversation_messages(db, conversation_id, limit)
        
        return {
            "success": True,
            "conversation_id": conversation_id,
            "messages": [
                {
                    "id": msg.id,
                    "message_type": msg.message_type,
                    "content": msg.content,
                    "created_at": msg.created_at.isoformat(),
                    "tokens_used": msg.tokens_used,
                    "suggestions": msg.message_metadata.get("suggestions", []) if msg.message_metadata else []
                }
                for msg in messages
            ],
            "total": len(messages)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo mensajes de conversación: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor"
        )
```

## 🎯 **Flujo de Trabajo Actualizado**

### **Nueva Conversación:**
```
Usuario conecta → No hay conversación activa → Crear nueva conversación → Enviar mensaje de bienvenida
```

### **Conversación Existente:**
```
Usuario conecta → Hay conversación activa → Cargar historial → Mostrar mensajes anteriores
```

## 📊 **Ventajas de esta Solución**

### **Para el Usuario:**
- ✅ **Continúa donde lo dejó** - Ve el historial de la conversación
- ✅ **No pierde contexto** - Mantiene la conversación anterior
- ✅ **Experiencia fluida** - No se repite el mensaje de bienvenida

### **Para el Sistema:**
- ✅ **Eficiente** - No duplica mensajes
- ✅ **Consistente** - Misma experiencia para todos los roles
- ✅ **Funcional** - Mantiene el historial de conversaciones

## 🔧 **Implementación Paso a Paso**

### **Paso 1: Crear endpoint para obtener mensajes**
- Agregar endpoint en `backend/src/chat/router.py`
- Implementar función en `ChatLoggingService`

### **Paso 2: Modificar WebSocket router**
- Agregar función `send_conversation_history`
- Agregar función `get_conversation_messages`
- Modificar lógica de conexión

### **Paso 3: Probar funcionalidad**
- Probar con conversación nueva
- Probar con conversación existente
- Verificar que se muestra el historial

## 🚀 **Resultado Final**

- **Nueva conversación**: Mensaje de bienvenida con comandos
- **Conversación existente**: Historial de mensajes anteriores
- **Experiencia consistente**: Para todos los roles (admin, jefe_seguridad, etc.)

¿Quieres que implemente esta solución para mostrar el historial en lugar del mensaje de bienvenida?



