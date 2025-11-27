# ⏰ Sistema de Recordatorios para Estado waiting_DPS

## 🎯 **Descripción del Sistema**

### **Estado**: `waiting_DPS` (waiting_DPS)
- **Cuándo se activa**: Al detectar correo automático del gobierno
- **Duración total**: 2 meses (8 semanas)
- **Acción requerida**: Usuario debe rellenar y enviar documento

## 📅 **Cronograma de Recordatorios**

### **FASE 1: Primer Mes (Semanas 1-4)**
- **Frecuencia**: **Semanal** (cada lunes)
- **Total de recordatorios**: 4
- **Días**: Lunes de cada semana
- **Horario**: Laboral (9:00 AM - 6:00 PM)

### **FASE 2: Segundo Mes - Primera Parte (Semanas 5-7)**
- **Frecuencia**: **Cada 3 días**
- **Total de recordatorios**: 7
- **Días**: Lunes, Jueves, Lunes, Jueves, Lunes, Jueves, Lunes
- **Horario**: Laboral (9:00 AM - 6:00 PM)

### **FASE 3: Segunda Parte - Última Semana (Semana 8)**
- **Frecuencia**: **Diaria**
- **Total de recordatorios**: 5
- **Días**: Lunes a Viernes
- **Horario**: Laboral (9:00 AM - 6:00 PM)

## 📊 **Resumen Total de Recordatorios**

| Fase | Duración | Frecuencia | Recordatorios | Total |
|------|----------|------------|---------------|-------|
| Fase 1 | Semanas 1-4 | Semanal (Lunes) | 4 | 4 |
| Fase 2 | Semanas 5-7 | Cada 3 días | 7 | 11 |
| Fase 3 | Semana 8 | Diaria (L-V) | 5 | 16 |
| **TOTAL** | **8 semanas** | **Variable** | **16** | **16** |

## 🕐 **Horario Laboral y Días Lectivos**

### **Horario Laboral:**
- **Inicio**: 9:00 AM
- **Fin**: 6:00 PM
- **Zona horaria**: Local del sistema

### **Días Lectivos:**
- **Lunes a Viernes** (L-V)
- **Excluir**: Sábados, domingos y festivos
- **Consideración de festivos**: Si es posible detectar automáticamente

## 📧 **Contenido del Recordatorio**

### **Template**: `reminder` (actualizado)
### **Asunto**: `Recordatorio: Documento DPS pendiente - [Documento]`

### **Contenido del Email:**
```
Estimado/a [Nombre],

Su solicitud HPS está en estado waiting_DPS y requiere su acción.

Detalles:
- Número de documento: [Documento]
- Estado actual: waiting_DPS
- Días transcurridos: [X] días
- Tiempo restante: [Y] días
- Fecha límite: [Fecha límite]

Acción requerida:
- Rellenar documento DPS
- Enviar documento completado
- Seguir instrucciones del gobierno

Si no completa la acción en el tiempo establecido, su solicitud puede ser cancelada.

Atentamente,
Equipo HPS System
```

## 🔧 **Implementación Técnica**

### **1. Nuevo Template de Recordatorio DPS**
```python
# backend/src/email/templates/reminder_dps.py
class ReminderDPSTemplate:
    @staticmethod
    def get_template(data: EmailTemplateData) -> Dict[str, str]:
        # Template específico para recordatorios DPS
        pass
```

### **2. Servicio de Recordatorios DPS**
```python
# backend/src/email/dps_reminder_service.py
class DPSReminderService:
    def schedule_dps_reminders(self, hps_request_id: int):
        """Programa recordatorios para HPS en estado waiting_DPS"""
        pass
    
    def send_weekly_reminder(self, hps_request_id: int):
        """Envía recordatorio semanal (Fase 1)"""
        pass
    
    def send_biweekly_reminder(self, hps_request_id: int):
        """Envía recordatorio cada 3 días (Fase 2)"""
        pass
    
    def send_daily_reminder(self, hps_request_id: int):
        """Envía recordatorio diario (Fase 3)"""
        pass
```

### **3. Tareas Celery Programadas**
```python
# backend/src/tasks/dps_reminder_tasks.py
@celery_app.task
def send_dps_weekly_reminders():
    """Envía recordatorios semanales (Fase 1)"""
    pass

@celery_app.task
def send_dps_biweekly_reminders():
    """Envía recordatorios cada 3 días (Fase 2)"""
    pass

@celery_app.task
def send_dps_daily_reminders():
    """Envía recordatorios diarios (Fase 3)"""
    pass
```

### **4. Configuración de Tareas Programadas**
```python
# Configuración Celery Beat
CELERY_BEAT_SCHEDULE = {
    'dps-weekly-reminders': {
        'task': 'dps_reminder.weekly',
        'schedule': crontab(hour=9, minute=0, day_of_week=1),  # Lunes 9:00 AM
    },
    'dps-biweekly-reminders': {
        'task': 'dps_reminder.biweekly',
        'schedule': crontab(hour=9, minute=0, day_of_week='1,4'),  # Lunes y Jueves 9:00 AM
    },
    'dps-daily-reminders': {
        'task': 'dps_reminder.daily',
        'schedule': crontab(hour=9, minute=0, day_of_week='1-5'),  # L-V 9:00 AM
    },
}
```

## 🎯 **Flujo de Trabajo**

### **1. Activación del Sistema**
```
Correo gobierno detectado → Estado cambia a waiting_DPS → Sistema programa recordatorios
```

### **2. Fase 1 (Semanas 1-4)**
```
Cada lunes 9:00 AM → Verificar HPS en waiting_DPS → Enviar recordatorio semanal
```

### **3. Fase 2 (Semanas 5-7)**
```
Lunes y Jueves 9:00 AM → Verificar HPS en waiting_DPS → Enviar recordatorio cada 3 días
```

### **4. Fase 3 (Semana 8)**
```
Lunes a Viernes 9:00 AM → Verificar HPS en waiting_DPS → Enviar recordatorio diario
```

## 📊 **Base de Datos**

### **Nueva Tabla: `dps_reminder_schedule`**
```sql
CREATE TABLE dps_reminder_schedule (
    id SERIAL PRIMARY KEY,
    hps_request_id INTEGER REFERENCES hps_requests(id),
    status VARCHAR(20) DEFAULT 'waiting_dps',
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    current_phase INTEGER DEFAULT 1,
    reminders_sent INTEGER DEFAULT 0,
    last_reminder_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### **Campos de Control:**
- `current_phase`: 1 (semanal), 2 (cada 3 días), 3 (diario)
- `reminders_sent`: Contador de recordatorios enviados
- `last_reminder_date`: Fecha del último recordatorio
- `end_date`: Fecha límite (2 meses después del start_date)

## 🚀 **Implementación Paso a Paso**

### **Paso 1: Crear Template de Recordatorio DPS**
- Template específico para waiting_DPS
- Contenido personalizado según fase
- Información de días restantes

### **Paso 2: Implementar Servicio de Recordatorios**
- Lógica de fases
- Cálculo de días restantes
- Envío de recordatorios

### **Paso 3: Configurar Tareas Celery**
- Tareas programadas por fase
- Configuración de horarios
- Manejo de días festivos

### **Paso 4: Integrar con Sistema Existente**
- Modificar monitor de correos
- Actualizar estados
- Programar recordatorios automáticamente

## 📈 **Beneficios del Sistema**

### **Para el Usuario:**
- ✅ **Recordatorios progresivos** - No abruma al inicio
- ✅ **Información clara** - Sabe exactamente qué hacer
- ✅ **Tiempo suficiente** - 2 meses para completar
- ✅ **Horario laboral** - No molesta fuera del trabajo

### **Para el Sistema:**
- ✅ **Automatización completa** - Sin intervención manual
- ✅ **Escalabilidad** - Maneja múltiples HPS simultáneamente
- ✅ **Flexibilidad** - Fácil modificar frecuencias
- ✅ **Eficiencia** - Reduce solicitudes perdidas

## 🎯 **Estado del Sistema**

### **Pendiente de Implementación:**
- [ ] Template de recordatorio DPS
- [ ] Servicio de recordatorios DPS
- [ ] Tareas Celery programadas
- [ ] Tabla de base de datos
- [ ] Integración con monitor de correos
- [ ] Pruebas del sistema

### **Sistema Actual:**
- ✅ **Recordatorio genérico** - Funcionando
- ✅ **Templates modulares** - Implementados
- ✅ **Sistema de envío** - Verificado
- ✅ **Base técnica** - Lista para extensión

¿Quieres que implemente este sistema de recordatorios escalonados para el estado `waiting_DPS`?



