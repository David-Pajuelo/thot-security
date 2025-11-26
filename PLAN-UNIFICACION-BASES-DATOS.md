# Plan de Unificación de Bases de Datos: HPS-System → CryptoTrace

## 📋 Resumen Ejecutivo

Este documento detalla el plan exhaustivo para unificar las bases de datos de `hps-system` (FastAPI + SQLAlchemy) y `cryptotrace` (Django) en una única base de datos PostgreSQL gestionada por Django.

**Objetivo:** Migrar todos los datos de `hps-system` a la base de datos de `cryptotrace`, unificando usuarios, roles, equipos, solicitudes HPS, tokens, plantillas, logs de auditoría y conversaciones de chat.

---

## 🔍 Estado Actual

### Base de Datos HPS-System (SQLAlchemy)

**Ubicación:** Base de datos PostgreSQL separada (o compartida en desarrollo)

**Modelos principales:**
- `users` - Usuarios del sistema (UUID, email, password_hash, first_name, last_name, role_id, team_id)
- `roles` - Roles del sistema (id, name, description, permissions JSON)
- `teams` - Equipos de trabajo (UUID, name, description, team_lead_id)
- `hps_requests` - Solicitudes HPS (UUID, user_id, request_type, status, datos personales, PDFs)
- `hps_tokens` - Tokens para formularios públicos (UUID, token, email, purpose, expires_at)
- `hps_templates` - Plantillas PDF (id, name, template_pdf, template_type, version)
- `audit_logs` - Logs de auditoría (UUID, user_id, action, table_name, old_values, new_values)
- `chat_conversations` - Conversaciones de chat IA (UUID, user_id, session_id, status, conversation_data JSON)
- `chat_messages` - Mensajes de chat (UUID, conversation_id, message_type, content)
- `chat_metrics` - Métricas de chat (id, date, total_conversations)

### Base de Datos CryptoTrace (Django)

**Ubicación:** Base de datos PostgreSQL (`cryptotrace`)

**Modelos principales:**

**Sistema de Autenticación:**
- `auth_user` - Usuario nativo de Django (id, username, email, password, first_name, last_name, is_active, is_staff, is_superuser, date_joined)
- `productos_userprofile` - Perfil extendido (OneToOne con User, must_change_password)

**HPS Core (ya migrado):**
- `hps_core_hpsrole` - Roles HPS (id, name, description, permissions JSON)
- `hps_core_hpsteam` - Equipos HPS (UUID, name, description, team_lead FK)
- `hps_core_hpsteammembership` - Membresías de equipos (user FK, team FK)
- `hps_core_hpsuserprofile` - Perfil HPS extendido (OneToOne con User, role FK, team FK, email_verified, is_temp_password, etc.)
- `hps_core_hpsrequest` - Solicitudes HPS (UUID, user FK, request_type, status, datos personales, PDFs)
- `hps_core_hpstoken` - Tokens HPS (UUID, token, email, purpose, expires_at)
- `hps_core_hpstemplate` - Plantillas HPS (id, name, template_pdf, template_type, version)
- `hps_core_hpsauditlog` - Logs de auditoría HPS (id, user FK, action, resource_type, resource_id, old_values, new_values)

**Productos (dominio CryptoTrace):**
- `productos_tipoproducto` - Tipos de productos
- `productos_catalogoproducto` - Catálogo de productos
- `productos_inventarioproducto` - Inventario
- `productos_albaran` - Albaranes AC21
- `productos_movimientoproducto` - Movimientos
- `productos_lineatemporalproducto` - Líneas temporales
- `productos_empresa` - Empresas

---

## 🎯 Estrategia de Unificación

### Principio Fundamental
**Django User será el modelo único de usuarios.** Todos los usuarios de `hps-system` se migrarán a `auth_user` de Django, y la información adicional se almacenará en `hps_core_hpsuserprofile`.

### Mapeo de Modelos

| HPS-System (SQLAlchemy) | CryptoTrace (Django) | Estrategia |
|-------------------------|----------------------|------------|
| `users` | `auth_user` + `hps_core_hpsuserprofile` | Migrar a User Django, datos adicionales en HpsUserProfile |
| `roles` | `hps_core_hpsrole` | ✅ Ya migrado, solo ETL de datos |
| `teams` | `hps_core_hpsteam` | ✅ Ya migrado, solo ETL de datos |
| `hps_requests` | `hps_core_hpsrequest` | ✅ Ya migrado, solo ETL de datos |
| `hps_tokens` | `hps_core_hpstoken` | ✅ Ya migrado, solo ETL de datos |
| `hps_templates` | `hps_core_hpstemplate` | ✅ Ya migrado, solo ETL de datos |
| `audit_logs` | `hps_core_hpsauditlog` | ✅ Ya migrado, solo ETL de datos |
| `chat_conversations` | **NUEVO** - Crear modelo Django | Crear modelo y migrar datos |
| `chat_messages` | **NUEVO** - Crear modelo Django | Crear modelo y migrar datos |
| `chat_metrics` | **NUEVO** - Crear modelo Django | Crear modelo y migrar datos |

---

## 📝 Plan de Ejecución Detallado

### FASE 1: Preparación y Análisis (1-2 días)

#### 1.1 Inventario de Datos
- [ ] Exportar dump completo de base de datos HPS-System
- [ ] Analizar volumen de datos por tabla
- [ ] Identificar relaciones y dependencias
- [ ] Detectar datos duplicados o conflictos potenciales
- [ ] Documentar usuarios existentes en ambos sistemas

**Comandos:**
```bash
# Exportar dump de HPS
pg_dump -h localhost -U postgres -d hps_db > hps_backup_$(date +%Y%m%d).sql

# Analizar tablas
psql -h localhost -U postgres -d hps_db -c "\dt"
psql -h localhost -U postgres -d hps_db -c "SELECT table_name, pg_size_pretty(pg_total_relation_size('\"'||table_name||'\"')) FROM information_schema.tables WHERE table_schema = 'public';"
```

#### 1.2 Verificación de Modelos Django
- [ ] Verificar que todos los modelos HPS en Django estén correctamente definidos
- [ ] Comparar campos entre SQLAlchemy y Django
- [ ] Identificar campos faltantes o diferencias de tipos
- [ ] Documentar mapeo de campos detallado

#### 1.3 Crear Modelos Faltantes
- [ ] Crear modelo `ChatConversation` en Django
- [ ] Crear modelo `ChatMessage` en Django
- [ ] Crear modelo `ChatMetrics` en Django
- [ ] Generar migraciones para nuevos modelos

---

### FASE 2: Desarrollo de Scripts ETL (2-3 días)

#### 2.1 Script de Migración de Usuarios

**Objetivo:** Migrar usuarios de `hps-system.users` a `auth_user` + `hps_core_hpsuserprofile`

**Consideraciones:**
- Los usuarios de HPS usan UUID como ID, Django User usa Integer
- Necesitamos mapear UUID → Integer y mantener referencia
- Password hash debe ser compatible (ambos usan bcrypt/argon2)
- Email debe ser único en Django
- `first_name` y `last_name` deben mapearse correctamente

**Estructura del script:**
```python
# cryptotrace/cryptotrace-backend/src/hps_core/management/commands/migrate_hps_users.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
import psycopg2
from psycopg2.extras import RealDictCursor

User = get_user_model()

class Command(BaseCommand):
    help = 'Migra usuarios de hps-system a Django'
    
    def add_arguments(self, parser):
        parser.add_argument('--hps-db-url', type=str, required=True)
        parser.add_argument('--dry-run', action='store_true')
    
    def handle(self, *args, **options):
        # 1. Conectar a base HPS
        # 2. Leer usuarios
        # 3. Para cada usuario:
        #    - Crear User Django (username = email, email = email)
        #    - Crear HpsUserProfile
        #    - Mapear role_id → HpsRole
        #    - Mapear team_id → HpsTeam
        #    - Guardar UUID original en campo custom o tabla de mapeo
        # 4. Validar integridad
```

**Tabla de mapeo UUID → User ID:**
Crear tabla temporal `hps_user_mapping` para mantener referencia:
```python
class HpsUserMapping(models.Model):
    hps_user_uuid = models.UUIDField(unique=True)
    django_user = models.OneToOneField(User, on_delete=models.CASCADE)
    migrated_at = models.DateTimeField(auto_now_add=True)
```

#### 2.2 Script de Migración de Roles

**Objetivo:** Migrar roles de `hps-system.roles` a `hps_core_hpsrole`

**Consideraciones:**
- Los roles en HPS usan Integer ID, Django usa AutoField (compatible)
- Verificar que no existan roles duplicados por nombre
- Preservar `permissions` JSON

**Estructura:**
```python
# migrate_hps_roles.py
def migrate_roles(hps_conn, django_db):
    hps_roles = fetch_hps_roles(hps_conn)
    for role in hps_roles:
        django_role, created = HpsRole.objects.get_or_create(
            name=role['name'],
            defaults={
                'description': role['description'],
                'permissions': role['permissions']
            }
        )
        # Guardar mapeo role_id_hps -> role_id_django
```

#### 2.3 Script de Migración de Equipos

**Objetivo:** Migrar equipos de `hps-system.teams` a `hps_core_hpsteam`

**Consideraciones:**
- Equipos usan UUID (compatible con Django)
- `team_lead_id` debe mapearse usando tabla de mapeo de usuarios
- Verificar que UUIDs no colisionen

#### 2.4 Script de Migración de Solicitudes HPS

**Objetivo:** Migrar `hps_requests` a `hps_core_hpsrequest`

**Consideraciones:**
- UUIDs son compatibles
- `user_id`, `submitted_by`, `approved_by` deben mapearse usando tabla de mapeo
- `template_id` debe mapearse (Integer → Integer, pero verificar correspondencia)
- PDFs almacenados como LargeBinary en HPS, FileField en Django (necesita conversión)

**Manejo de PDFs:**

Este es uno de los aspectos más críticos de la migración. Los PDFs en HPS-System están almacenados como **LargeBinary** (directamente en la base de datos PostgreSQL), mientras que en Django se usan **FileField** (archivos en el filesystem, solo se guarda la ruta en la BD).

**Diferencia entre LargeBinary y FileField:**

1. **LargeBinary (HPS-System):**
   - Los archivos PDF se almacenan como datos binarios directamente en la columna de la base de datos
   - Ventaja: Todo está en un solo lugar (la BD)
   - Desventaja: La base de datos crece mucho, backups más pesados, consultas más lentas

2. **FileField (Django):**
   - Los archivos se guardan en el filesystem (carpeta `media/`)
   - En la base de datos solo se guarda la ruta relativa (ej: `hps/filled/uuid_123.pdf`)
   - Ventaja: Base de datos más ligera, mejor performance, más fácil de gestionar
   - Desventaja: Necesita gestionar filesystem y backups separados

**Proceso de Conversión Detallado:**

```python
import os
from django.core.files.base import ContentFile
from django.conf import settings
from pathlib import Path

def convert_largebinary_to_filefield(hps_binary_data, upload_to_path, filename):
    """
    Convierte un LargeBinary de HPS a FileField de Django
    
    Args:
        hps_binary_data: bytes - Datos binarios del PDF desde HPS
        upload_to_path: str - Ruta relativa donde guardar (ej: "hps/filled/")
        filename: str - Nombre del archivo (ej: "hps_request_uuid.pdf")
    
    Returns:
        str - Ruta relativa del archivo guardado (para asignar a FileField)
    """
    if not hps_binary_data:
        return None
    
    # 1. Validar que sean datos binarios válidos
    if not isinstance(hps_binary_data, bytes):
        raise ValueError(f"Expected bytes, got {type(hps_binary_data)}")
    
    # 2. Validar que sea un PDF (magic bytes: %PDF)
    if not hps_binary_data.startswith(b'%PDF'):
        raise ValueError("Invalid PDF file: missing PDF header")
    
    # 3. Crear directorio si no existe
    media_root = Path(settings.MEDIA_ROOT)
    target_dir = media_root / upload_to_path
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # 4. Generar ruta completa del archivo
    file_path = target_dir / filename
    
    # 5. Escribir archivo en filesystem
    with open(file_path, 'wb') as f:
        f.write(hps_binary_data)
    
    # 6. Retornar ruta relativa (lo que Django guarda en FileField)
    return f"{upload_to_path}{filename}"


def migrate_hps_request_pdfs(hps_request_row, django_hps_request):
    """
    Migra los PDFs de una solicitud HPS desde LargeBinary a FileField
    
    Args:
        hps_request_row: dict - Fila de hps_requests desde HPS
        django_hps_request: HpsRequest - Instancia Django ya creada
    """
    hps_id = str(hps_request_row['id'])
    
    # Migrar filled_pdf
    if hps_request_row.get('filled_pdf'):
        try:
            filename_filled = f"hps_request_{hps_id}_filled.pdf"
            relative_path = convert_largebinary_to_filefield(
                hps_binary_data=hps_request_row['filled_pdf'],
                upload_to_path="hps/filled/",
                filename=filename_filled
            )
            django_hps_request.filled_pdf.name = relative_path
            django_hps_request.save(update_fields=['filled_pdf'])
            logger.info(f"Migrado filled_pdf para HPS {hps_id}")
        except Exception as e:
            logger.error(f"Error migrando filled_pdf para HPS {hps_id}: {str(e)}")
            # Continuar sin el PDF, pero registrar el error
    
    # Migrar response_pdf
    if hps_request_row.get('response_pdf'):
        try:
            filename_response = f"hps_request_{hps_id}_response.pdf"
            relative_path = convert_largebinary_to_filefield(
                hps_binary_data=hps_request_row['response_pdf'],
                upload_to_path="hps/responses/",
                filename=filename_response
            )
            django_hps_request.response_pdf.name = relative_path
            django_hps_request.save(update_fields=['response_pdf'])
            logger.info(f"Migrado response_pdf para HPS {hps_id}")
        except Exception as e:
            logger.error(f"Error migrando response_pdf para HPS {hps_id}: {str(e)}")
```

**Estructura de Directorios Resultante:**

```
media/
├── hps/
│   ├── filled/
│   │   ├── hps_request_550e8400-e29b-41d4-a716-446655440000_filled.pdf
│   │   ├── hps_request_660e8400-e29b-41d4-a716-446655440001_filled.pdf
│   │   └── ...
│   ├── responses/
│   │   ├── hps_request_550e8400-e29b-41d4-a716-446655440000_response.pdf
│   │   └── ...
│   └── templates/
│       ├── template_1_jefe_seguridad_v1.0.pdf
│       ├── template_2_suplente_v1.0.pdf
│       └── ...
```

**Consideraciones Importantes:**

1. **Espacio en Disco:**
   - Verificar que haya suficiente espacio antes de migrar
   - Los PDFs pueden ser grandes (1-10 MB cada uno)
   - Calcular: `número_registros × tamaño_promedio_pdf × 2` (filled + response)

2. **Validación de Integridad:**
   ```python
   def validate_pdf_integrity(original_binary, saved_file_path):
       """Valida que el PDF migrado sea idéntico al original"""
       with open(saved_file_path, 'rb') as f:
           saved_binary = f.read()
       
       # Comparar tamaños
       if len(original_binary) != len(saved_binary):
           return False
       
       # Comparar contenido (hash)
       import hashlib
       original_hash = hashlib.md5(original_binary).hexdigest()
       saved_hash = hashlib.md5(saved_binary).hexdigest()
       
       return original_hash == saved_hash
   ```

3. **Manejo de Errores:**
   - Si un PDF está corrupto, registrar error pero continuar
   - Mantener referencia al PDF original en la BD HPS por si acaso
   - Generar reporte de PDFs que fallaron

4. **Performance:**
   - Migrar en lotes (batch) para no saturar memoria
   - Usar streaming para PDFs muy grandes
   - Considerar procesamiento asíncrono con Celery

5. **Nombres de Archivo:**
   - Usar UUID de la solicitud para evitar colisiones
   - Incluir sufijo `_filled` o `_response` para claridad
   - Mantener extensión `.pdf` para compatibilidad

**Script Completo de Migración de PDFs:**

```python
def migrate_all_hps_pdfs(hps_cursor, batch_size=100):
    """
    Migra todos los PDFs de solicitudes HPS en lotes
    
    Args:
        hps_cursor: cursor de base HPS
        batch_size: número de registros por lote
    """
    # Contar total
    hps_cursor.execute("SELECT COUNT(*) FROM hps_requests WHERE filled_pdf IS NOT NULL OR response_pdf IS NOT NULL")
    total = hps_cursor.fetchone()['count']
    
    logger.info(f"Iniciando migración de PDFs: {total} solicitudes con PDFs")
    
    offset = 0
    migrated = 0
    errors = 0
    
    while offset < total:
        # Obtener lote
        hps_cursor.execute("""
            SELECT id, filled_pdf, response_pdf 
            FROM hps_requests 
            WHERE filled_pdf IS NOT NULL OR response_pdf IS NOT NULL
            LIMIT %s OFFSET %s
        """, (batch_size, offset))
        
        batch = hps_cursor.fetchall()
        
        for row in batch:
            hps_id = row['id']
            try:
                # Obtener instancia Django
                django_request = HpsRequest.objects.get(id=hps_id)
                
                # Migrar PDFs
                migrate_hps_request_pdfs(row, django_request)
                migrated += 1
                
            except HpsRequest.DoesNotExist:
                logger.warning(f"HPS request {hps_id} no encontrado en Django")
                errors += 1
            except Exception as e:
                logger.error(f"Error migrando PDFs para HPS {hps_id}: {str(e)}")
                errors += 1
        
        offset += batch_size
        logger.info(f"Progreso: {migrated}/{total} migrados, {errors} errores")
    
    logger.info(f"Migración de PDFs completada: {migrated} exitosos, {errors} errores")
    return migrated, errors
```

**Validación Post-Migración:**

```python
def validate_pdf_migration():
    """Valida que todos los PDFs se hayan migrado correctamente"""
    from django.core.files.storage import default_storage
    
    # Contar PDFs en HPS
    hps_cursor.execute("""
        SELECT COUNT(*) as total,
               COUNT(filled_pdf) as filled_count,
               COUNT(response_pdf) as response_count
        FROM hps_requests
    """)
    hps_stats = hps_cursor.fetchone()
    
    # Contar PDFs en Django
    django_filled = HpsRequest.objects.exclude(filled_pdf='').count()
    django_response = HpsRequest.objects.exclude(response_pdf='').count()
    
    # Verificar que archivos existan en filesystem
    django_requests = HpsRequest.objects.exclude(filled_pdf='')
    filesystem_ok = 0
    filesystem_missing = 0
    
    for req in django_requests:
        if req.filled_pdf and default_storage.exists(req.filled_pdf.name):
            filesystem_ok += 1
        else:
            filesystem_missing += 1
            logger.error(f"PDF faltante en filesystem: {req.filled_pdf.name}")
    
    logger.info(f"""
    Validación de PDFs:
    - HPS filled_pdf: {hps_stats['filled_count']}
    - Django filled_pdf: {django_filled}
    - Archivos en filesystem: {filesystem_ok}
    - Archivos faltantes: {filesystem_missing}
    """)
    
    return filesystem_missing == 0
```

#### 2.5 Script de Migración de Tokens

**Objetivo:** Migrar `hps_tokens` a `hps_core_hpstoken`

**Consideraciones:**
- UUIDs compatibles
- `requested_by` debe mapearse usando tabla de mapeo
- Tokens deben preservarse exactamente (son únicos)

#### 2.6 Script de Migración de Plantillas

**Objetivo:** Migrar `hps_templates` a `hps_core_hpstemplate`

**Consideraciones:**
- IDs Integer compatibles
- PDFs necesitan conversión de LargeBinary a FileField
- Verificar que no existan duplicados

#### 2.7 Script de Migración de Logs de Auditoría

**Objetivo:** Migrar `audit_logs` a `hps_core_hpsauditlog`

**Consideraciones:**
- `user_id` debe mapearse
- `record_id` puede referenciar diferentes tablas (necesita mapeo según `table_name`)
- Preservar timestamps exactos

#### 2.8 Script de Migración de Chat (NUEVO)

**Objetivo:** Crear modelos Django y migrar datos de chat

**Pasos:**
1. Crear modelos Django:
   - `ChatConversation` (UUID, user FK, session_id, status, conversation_data JSON)
   - `ChatMessage` (UUID, conversation FK, message_type, content, timestamp)
   - `ChatMetrics` (id, date, total_conversations, etc.)

2. Generar migraciones:
   ```bash
   python manage.py makemigrations hps_core
   ```

3. Script de migración:
   ```python
   # migrate_hps_chat.py
   def migrate_chat_data(hps_conn, django_db):
       # Migrar conversaciones
       # Migrar mensajes (mantener FK a conversaciones)
       # Migrar métricas
   ```

---

### FASE 3: Validación y Pruebas (1-2 días)

#### 3.1 Validación de Integridad Referencial
- [ ] Verificar que todos los ForeignKeys estén correctamente mapeados
- [ ] Validar que no haya referencias huérfanas
- [ ] Comprobar que UUIDs se preserven correctamente
- [ ] Verificar que emails sean únicos

#### 3.2 Validación de Datos
- [ ] Comparar conteos de registros (antes vs después)
- [ ] Validar que todos los usuarios tengan perfil HPS
- [ ] Verificar que roles y equipos estén correctamente asignados
- [ ] Comprobar que PDFs se hayan migrado correctamente

#### 3.3 Pruebas Funcionales
- [ ] Probar login con usuarios migrados
- [ ] Verificar que permisos funcionen correctamente
- [ ] Probar acceso a solicitudes HPS migradas
- [ ] Validar que tokens funcionen
- [ ] Probar endpoints de API con datos migrados

---

### FASE 4: Ejecución de Migración (1 día)

#### 4.1 Preparación
- [ ] Crear backup completo de ambas bases de datos
- [ ] Verificar espacio en disco suficiente
- [ ] Notificar a usuarios (si aplica)
- [ ] Poner sistema en modo mantenimiento (opcional)

#### 4.2 Ejecución en Orden
1. **Roles** (sin dependencias)
2. **Equipos** (depende de usuarios para team_lead, pero podemos usar mapeo)
3. **Usuarios** (depende de roles)
4. **Actualizar equipos** con team_lead mapeado
5. **Plantillas** (sin dependencias críticas)
6. **Tokens** (depende de usuarios)
7. **Solicitudes HPS** (depende de usuarios, plantillas)
8. **Logs de auditoría** (depende de usuarios)
9. **Chat** (depende de usuarios)

#### 4.3 Post-Migración
- [ ] Ejecutar validaciones automáticas
- [ ] Generar reporte de migración
- [ ] Actualizar configuraciones que referencien base HPS
- [ ] Limpiar tablas temporales de mapeo (opcional, mantener por seguridad)

---

### FASE 5: Consolidación y Limpieza (1 día)

#### 5.1 Actualización de Referencias
- [ ] Actualizar código que use IDs de HPS para usar IDs de Django
- [ ] Actualizar configuraciones de servicios externos
- [ ] Actualizar documentación

#### 5.2 Deprecación de Base HPS
- [ ] Marcar base HPS como "read-only" (opcional, mantener como backup)
- [ ] Documentar proceso de rollback si es necesario
- [ ] Planificar eliminación futura (después de validación extendida)

---

## 🔧 Scripts ETL Detallados

### Script Principal de Migración

```python
# cryptotrace/cryptotrace-backend/src/hps_core/management/commands/migrate_hps_database.py

from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from datetime import datetime

User = get_user_model()

class Command(BaseCommand):
    help = 'Migra toda la base de datos de hps-system a cryptotrace'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--hps-db-url',
            type=str,
            required=True,
            help='URL de conexión a base HPS: postgresql://user:pass@host:port/dbname'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Ejecutar sin guardar cambios'
        )
        parser.add_argument(
            '--skip-users',
            action='store_true',
            help='Saltar migración de usuarios'
        )
        parser.add_argument(
            '--skip-chat',
            action='store_true',
            help='Saltar migración de chat'
        )
    
    def handle(self, *args, **options):
        hps_db_url = options['hps_db_url']
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('MODO DRY-RUN: No se guardarán cambios'))
        
        # Conectar a base HPS
        hps_conn = psycopg2.connect(hps_db_url)
        hps_cursor = hps_conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            # Crear tabla de mapeo
            self.create_mapping_tables()
            
            # Ejecutar migraciones en orden
            if not options['skip_users']:
                self.migrate_roles(hps_cursor, dry_run)
                self.migrate_teams(hps_cursor, dry_run)
                self.migrate_users(hps_cursor, dry_run)
                self.update_team_leads(hps_cursor, dry_run)
            
            self.migrate_templates(hps_cursor, dry_run)
            self.migrate_tokens(hps_cursor, dry_run)
            self.migrate_hps_requests(hps_cursor, dry_run)
            self.migrate_audit_logs(hps_cursor, dry_run)
            
            if not options['skip_chat']:
                self.migrate_chat(hps_cursor, dry_run)
            
            # Validaciones
            self.validate_migration(hps_cursor)
            
            if not dry_run:
                self.stdout.write(self.style.SUCCESS('Migración completada exitosamente'))
            else:
                self.stdout.write(self.style.WARNING('DRY-RUN completado'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error en migración: {str(e)}'))
            raise
        finally:
            hps_cursor.close()
            hps_conn.close()
    
    @transaction.atomic
    def migrate_roles(self, hps_cursor, dry_run):
        """Migrar roles"""
        self.stdout.write('Migrando roles...')
        # Implementación detallada
        pass
    
    @transaction.atomic
    def migrate_users(self, hps_cursor, dry_run):
        """Migrar usuarios"""
        self.stdout.write('Migrando usuarios...')
        # Implementación detallada
        pass
    
    # ... más métodos de migración
```

---

## 📊 Mapeo Detallado de Campos

### Usuarios

| HPS-System.users | Django auth_user | HpsUserProfile | Notas |
|------------------|------------------|----------------|-------|
| id (UUID) | - | - | Guardar en HpsUserMapping |
| email | email | - | Debe ser único |
| password_hash | password | - | Compatible (bcrypt/argon2) |
| first_name | first_name | - | Directo |
| last_name | last_name | - | Directo |
| role_id | - | role (FK) | Mapear usando tabla de roles |
| team_id | - | team (FK) | Mapear usando tabla de equipos |
| is_active | is_active | - | Directo |
| email_verified | - | email_verified | Directo |
| is_temp_password | - | is_temp_password | Directo |
| last_login | last_login | last_login | Directo |
| created_at | date_joined | - | Usar created_at |
| - | username | - | Usar email como username |

### Roles

| HPS-System.roles | HpsRole | Notas |
|------------------|---------|-------|
| id | id | AutoField, no preservar ID original |
| name | name | Único, verificar duplicados |
| description | description | Directo |
| permissions | permissions | JSON, directo |
| created_at | created_at | Directo |
| updated_at | updated_at | Directo |

### Equipos

| HPS-System.teams | HpsTeam | Notas |
|------------------|---------|-------|
| id (UUID) | id (UUID) | Preservar UUID |
| name | name | Directo |
| description | description | Directo |
| team_lead_id (UUID) | team_lead (FK) | Mapear usando HpsUserMapping |
| is_active | is_active | Directo |
| created_at | created_at | Directo |
| updated_at | updated_at | Directo |

### Solicitudes HPS

| HPS-System.hps_requests | HpsRequest | Notas |
|-------------------------|------------|-------|
| id (UUID) | id (UUID) | Preservar UUID |
| user_id (UUID) | user (FK) | Mapear usando HpsUserMapping |
| request_type | request_type | Directo |
| status | status | Directo |
| type | form_type | Mapear 'solicitud'/'traslado' |
| template_id | template (FK) | Mapear IDs de plantillas |
| filled_pdf (LargeBinary) | filled_pdf (FileField) | Convertir a archivo |
| response_pdf (LargeBinary) | response_pdf (FileField) | Convertir a archivo |
| document_type | document_type | Directo |
| document_number | document_number | Directo |
| ... (resto de campos) | ... | Directo |
| submitted_by (UUID) | submitted_by (FK) | Mapear usando HpsUserMapping |
| approved_by (UUID) | approved_by (FK) | Mapear usando HpsUserMapping |
| expires_at | expires_at | Directo |

---

## ⚠️ Consideraciones y Riesgos

### 1. Conflictos de Email
**Riesgo:** Usuarios con mismo email en ambos sistemas

**Mitigación:**
- Identificar duplicados antes de migrar
- Estrategia: Unificar usuarios o renombrar emails
- Crear reporte de conflictos

### 2. Password Hashes
**Riesgo:** Incompatibilidad entre sistemas de hash

**Mitigación:**
- Verificar que ambos usen el mismo algoritmo (bcrypt/argon2)
- Si difieren, forzar reset de contraseña o migrar con hash compatible

### 3. UUIDs vs Integer IDs
**Riesgo:** Pérdida de referencias al cambiar de UUID a Integer

**Mitigación:**
- Mantener tabla de mapeo `HpsUserMapping` permanentemente
- O usar UUID como primary key en User (requiere custom User model)

### 4. PDFs y Archivos
**Riesgo:** Pérdida de archivos durante conversión

**Mitigación:**
- Validar que todos los PDFs se hayan migrado
- Mantener backup de archivos originales
- Verificar integridad de archivos después de migración

### 5. Integridad Referencial
**Riesgo:** ForeignKeys rotos si mapeo falla

**Mitigación:**
- Validar todas las relaciones después de migración
- Usar transacciones para rollback automático
- Ejecutar validaciones exhaustivas

### 6. Datos de Chat
**Riesgo:** Modelos de chat no existen aún en Django

**Mitigación:**
- Crear modelos antes de migrar
- Validar estructura de JSON `conversation_data`
- Probar con datos de prueba primero

---

## 🧪 Plan de Pruebas

### Pruebas Unitarias
- [ ] Test de migración de usuarios individuales
- [ ] Test de migración de roles
- [ ] Test de migración de equipos
- [ ] Test de mapeo de ForeignKeys
- [ ] Test de conversión de PDFs

### Pruebas de Integración
- [ ] Test de migración completa en ambiente de desarrollo
- [ ] Test de rollback
- [ ] Test de validación de integridad
- [ ] Test de performance (tiempo de migración)

### Pruebas de Aceptación
- [ ] Login con usuarios migrados
- [ ] Acceso a solicitudes HPS migradas
- [ ] Funcionalidad de tokens
- [ ] Verificación de permisos y roles
- [ ] Acceso a historial de chat (si aplica)

---

## 📦 Estructura de Archivos a Crear

```
cryptotrace/cryptotrace-backend/src/hps_core/
├── management/
│   └── commands/
│       ├── migrate_hps_database.py      # Script principal
│       ├── migrate_hps_users.py         # Migración de usuarios
│       ├── migrate_hps_roles.py         # Migración de roles
│       ├── migrate_hps_teams.py          # Migración de equipos
│       ├── migrate_hps_requests.py      # Migración de solicitudes
│       ├── migrate_hps_tokens.py        # Migración de tokens
│       ├── migrate_hps_templates.py     # Migración de plantillas
│       ├── migrate_hps_audit_logs.py     # Migración de logs
│       ├── migrate_hps_chat.py          # Migración de chat
│       └── validate_migration.py        # Validaciones post-migración
├── models.py                            # Agregar modelos de chat
└── migrations/
    └── XXXX_add_chat_models.py         # Migración para chat
```

---

## 🔄 Plan de Rollback

### Si la migración falla:
1. **Detener migración inmediatamente**
2. **No hacer commit de transacciones**
3. **Restaurar backup de base CryptoTrace**
4. **Analizar logs de error**
5. **Corregir scripts y reintentar**

### Si se detectan problemas post-migración:
1. **Mantener base HPS como backup**
2. **Crear script de rollback selectivo**
3. **Documentar problemas encontrados**
4. **Planificar corrección incremental**

---

## 📅 Cronograma Estimado

| Fase | Duración | Dependencias |
|------|----------|--------------|
| FASE 1: Preparación | 1-2 días | - |
| FASE 2: Desarrollo ETL | 2-3 días | FASE 1 |
| FASE 3: Validación | 1-2 días | FASE 2 |
| FASE 4: Ejecución | 1 día | FASE 3 |
| FASE 5: Consolidación | 1 día | FASE 4 |
| **TOTAL** | **6-9 días** | - |

---

## ✅ Checklist de Ejecución

### Pre-Migración
- [ ] Backup completo de ambas bases de datos
- [ ] Verificar espacio en disco (mínimo 2x tamaño de datos)
- [ ] Crear modelos de chat en Django
- [ ] Generar migraciones de Django
- [ ] Probar scripts ETL en ambiente de desarrollo
- [ ] Documentar usuarios y datos críticos

### Durante Migración
- [ ] Ejecutar en orden: Roles → Equipos → Usuarios → Resto
- [ ] Validar cada paso antes de continuar
- [ ] Generar logs detallados
- [ ] Monitorear uso de recursos

### Post-Migración
- [ ] Ejecutar validaciones automáticas
- [ ] Verificar conteos de registros
- [ ] Probar funcionalidad crítica
- [ ] Generar reporte de migración
- [ ] Actualizar documentación
- [ ] Notificar a usuarios (si aplica)

---

## 📝 Notas Adicionales

### Opción: Custom User Model con UUID
Si se prefiere preservar UUIDs como primary key de User:
- Crear custom User model con UUIDField
- Requiere migración completa de Django auth
- Más complejo pero preserva referencias originales

### Opción: Mantener Base HPS como Read-Only
- Útil para consultas históricas
- Permite rollback si es necesario
- Requiere mantener conexión dual temporalmente

### Consideraciones de Performance
- Migraciones grandes pueden tardar horas
- Considerar migración en lotes (batch processing)
- Usar transacciones para integridad
- Monitorear locks de base de datos

---

## 🎯 Resultado Esperado

Al finalizar la migración:
- ✅ Todos los usuarios de HPS en `auth_user` de Django
- ✅ Todos los perfiles en `hps_core_hpsuserprofile`
- ✅ Todos los datos HPS en modelos Django correspondientes
- ✅ Modelos de chat creados y migrados
- ✅ Integridad referencial preservada
- ✅ Sistema funcionando con base de datos unificada
- ✅ Base HPS deprecada (mantener como backup)

---

**Documento creado:** 2025-01-24  
**Última actualización:** 2025-01-24  
**Autor:** Plan de Integración Thot-Security

