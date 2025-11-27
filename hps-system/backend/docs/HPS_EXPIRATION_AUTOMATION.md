# Automatización de Recordatorios de HPS Próximas a Caducar

Este documento describe la funcionalidad de automatización para enviar recordatorios cuando una HPS está próxima a caducar (exactamente 9 meses de antelación).

## 🎯 Funcionalidad

- **Verificación automática**: Busca HPS que caduquen exactamente en 9 meses
- **Envío de recordatorios**: Envía emails automáticos a los usuarios afectados UNA SOLA VEZ
- **Horario laboral**: Solo ejecuta en días laborales (L-V) entre 8:00 y 19:00
- **Configuración simple**: Sin interfaz web, solo automatización de fondo

## 📁 Archivos Creados

### Backend
- `src/tasks/hps_expiration_tasks.py` - Tareas de Celery para verificación
- `src/email/templates/hps_expiration_reminder.py` - Template de email para recordatorios
- `src/commands/check_hps_expiration.py` - Comando de verificación manual
- `scripts/setup_hps_expiration_automation.py` - Script de configuración

### Frontend
- **Sin componentes de frontend** - Solo automatización de fondo

## 🚀 Configuración

### 1. Configurar Automatización (Cron Job)

```bash
# Ejecutar script de configuración
python backend/scripts/setup_hps_expiration_automation.py setup

# Verificar estado
python backend/scripts/setup_hps_expiration_automation.py status

# Probar verificación manual
python backend/scripts/setup_hps_expiration_automation.py test
```

### 2. Configuración Manual de Cron

Si prefieres configurar manualmente:

```bash
# Editar crontab
crontab -e

# Agregar esta línea (ejecuta L-V a las 9:00 AM)
0 9 * * 1-5 cd /ruta/al/proyecto && python backend/src/commands/check_hps_expiration.py >> /var/log/hps_expiration_check.log 2>&1
```

### 3. Configuración en Docker

Para contenedores Docker, agregar al Dockerfile:

```dockerfile
# Instalar cron
RUN apt-get update && apt-get install -y cron

# Copiar script de configuración
COPY backend/scripts/setup_hps_expiration_automation.py /app/scripts/

# Configurar cron job (L-V a las 9:00 AM)
RUN echo "0 9 * * 1-5 cd /app && python backend/src/commands/check_hps_expiration.py >> /var/log/hps_expiration_check.log 2>&1" | crontab -

# Iniciar cron
CMD ["cron", "-f"]
```

## 🔧 Uso

### Verificación Manual

```bash
# Verificación manual (sin enviar emails)
python backend/src/commands/check_hps_expiration.py --manual

# Verificación completa (con envío de emails)
python backend/src/commands/check_hps_expiration.py
```

### Automatización

La automatización se ejecuta automáticamente:
- **Frecuencia**: Lunes a Viernes a las 9:00 AM
- **Horario laboral**: Solo entre 8:00 y 19:00
- **Período**: Exactamente 9 meses antes de la caducidad
- **Envío**: Una sola vez por HPS
- **Enlace de renovación**: Genera automáticamente un enlace seguro al formulario de renovación

## 🔗 Enlace de Renovación

Cada recordatorio incluye un enlace directo al formulario de renovación HPS:

- **Token seguro**: Generado automáticamente para cada usuario
- **Validez**: 72 horas desde la generación
- **Tipo**: Formulario de renovación (no nueva solicitud)
- **URL**: `http://localhost:3000/hps-form?token=XXX&email=XXX&type=renovacion`
- **Seguridad**: Token único por usuario y propósito

## 📧 Template de Email

El template de recordatorio incluye:

- **Información del usuario**: Nombre, email, DNI
- **Detalles de la HPS**: Fecha de caducidad, días restantes
- **Nivel de urgencia**: Visual basado en días restantes
  - 🚨 **URGENTE**: ≤ 30 días (rojo)
  - ⚠️ **IMPORTANTE**: ≤ 90 días (naranja)
  - ℹ️ **INFORMATIVO**: > 90 días (azul)
- **Enlace de renovación**: Botón directo al formulario de renovación HPS
- **Token seguro**: Enlace válido por 72 horas
- **Recomendaciones**: Iniciar renovación con 3 meses de antelación
- **Diseño responsive**: HTML con estilos modernos

## 🔍 Criterios de Búsqueda

La verificación busca HPS que cumplan:

- **Estado**: `approved` (aprobadas)
- **Fecha de caducidad**: No nula y exactamente en 9 meses
- **No caducadas**: Fecha de caducidad > fecha actual
- **Período fijo**: Exactamente 9 meses (no configurable)

## 📊 Logs y Monitoreo

### Logs de Verificación

```bash
# Ver logs de verificación automática
tail -f /var/log/hps_expiration_check.log

# Ver logs de Celery
celery -A src.celery_app worker --loglevel=info
```

### Monitoreo de Emails

Los emails se envían a través del sistema de email existente:

- **Logs de envío**: Disponibles en los logs de Celery
- **Estado de entrega**: Rastreado en la base de datos
- **Errores**: Registrados en logs del sistema

## 🛠️ Mantenimiento

### Verificar Estado

```bash
# Estado de la automatización
python backend/scripts/setup_hps_expiration_automation.py status

# Probar verificación
python backend/scripts/setup_hps_expiration_automation.py test
```

### Actualizar Configuración

```bash
# Reconfigurar cron job
python backend/scripts/setup_hps_expiration_automation.py setup
```

### Limpiar Logs

```bash
# Limpiar logs antiguos (opcional)
find /var/log -name "hps_expiration_check.log*" -mtime +30 -delete
```

## 🔒 Permisos

- **Verificación manual**: Solo administradores y managers
- **Envío de recordatorios**: Solo administradores y managers
- **Automatización**: Se ejecuta en background sin interfaz web

## 🐛 Solución de Problemas

### Error: "No se puede conectar a la base de datos"

```bash
# Verificar conexión
python -c "from src.database.database import check_db_connection; print(check_db_connection())"
```

### Error: "Template no encontrado"

```bash
# Verificar que el template esté registrado
python -c "from src.email.template_manager import TemplateManager; print(TemplateManager.get_available_templates())"
```

### Error: "Celery no está ejecutándose"

```bash
# Iniciar worker de Celery
celery -A src.celery_app worker --loglevel=info
```

### Error: "Cron job no ejecuta"

```bash
# Verificar crontab
crontab -l

# Verificar logs del sistema
grep CRON /var/log/syslog
```

## 📈 Métricas y Estadísticas

La funcionalidad proporciona:

- **Conteo de HPS encontradas**: Por período de búsqueda
- **Emails enviados**: Confirmación de envío
- **Errores de envío**: Registro de fallos
- **Fechas de verificación**: Historial de ejecuciones

## 🔄 Actualizaciones Futuras

Posibles mejoras:

- **Notificaciones escalonadas**: Recordatorios a 12, 6, 3, 1 meses
- **Personalización de templates**: Por tipo de HPS o empresa
- **Integración con calendarios**: Recordatorios en calendarios corporativos
- **Dashboard de métricas**: Estadísticas de caducidad y renovaciones
- **Notificaciones push**: Para usuarios con aplicaciones móviles

## 📞 Soporte

Para problemas o preguntas:

1. Revisar logs del sistema
2. Verificar configuración de cron
3. Probar verificación manual
4. Contactar al equipo de desarrollo

---

**Nota**: Esta funcionalidad requiere que el sistema de email esté configurado correctamente y que Celery esté ejecutándose para el procesamiento en background.
