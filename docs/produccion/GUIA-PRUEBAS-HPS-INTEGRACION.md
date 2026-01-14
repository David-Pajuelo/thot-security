# Guía de Pruebas - Integración HPS en CryptoTrace

## Estado Actual de la Integración

### ✅ Completado y Listo para Pruebas

#### 1. **Modelos Django**
- ✅ `HpsRole` - Roles del sistema HPS
- ✅ `HpsTeam` - Equipos de trabajo
- ✅ `HpsTeamMembership` - Membresías de usuarios a equipos
- ✅ `HpsUserProfile` - Perfiles extendidos de usuarios
- ✅ `HpsRequest` - Solicitudes HPS (completo con todos los campos)
- ✅ `HpsTemplate` - Plantillas PDF para formularios
- ✅ `HpsToken` - Tokens seguros para formularios públicos
- ✅ `HpsAuditLog` - Logs de auditoría

#### 2. **API REST (DRF)**
- ✅ `GET /api/v1/hps/roles/` - Listar roles
- ✅ `POST /api/v1/hps/roles/` - Crear rol
- ✅ `GET /api/v1/hps/teams/` - Listar equipos
- ✅ `POST /api/v1/hps/teams/` - Crear equipo
- ✅ `GET /api/v1/hps/requests/` - Listar solicitudes HPS (con filtros)
- ✅ `POST /api/v1/hps/requests/` - Crear solicitud HPS
- ✅ `GET /api/v1/hps/requests/{id}/` - Obtener solicitud
- ✅ `PUT /api/v1/hps/requests/{id}/` - Actualizar solicitud
- ✅ `DELETE /api/v1/hps/requests/{id}/` - Eliminar solicitud
- ✅ `POST /api/v1/hps/requests/{id}/approve/` - Aprobar solicitud
- ✅ `POST /api/v1/hps/requests/{id}/reject/` - Rechazar solicitud
- ✅ `GET /api/v1/hps/requests/stats/` - Estadísticas
- ✅ `GET /api/v1/hps/requests/team/{team_id}/` - Solicitudes por equipo
- ✅ `GET /api/v1/hps/requests/pending/` - Solicitudes pendientes
- ✅ `GET /api/v1/hps/requests/submitted/` - Solicitudes enviadas
- ✅ `POST /api/v1/hps/requests/public/` - Crear solicitud pública (con token)
- ✅ `GET /api/v1/hps/tokens/` - Listar tokens
- ✅ `POST /api/v1/hps/tokens/` - Crear token
- ✅ `GET /api/v1/hps/audit-logs/` - Listar logs de auditoría

#### 3. **Endpoints de Extensiones (Complemento Navegador)**
- ✅ `GET /api/v1/extension/personas?tipo=solicitud` - Personas pendientes
- ✅ `GET /api/v1/extension/persona/{dni}` - Datos de persona por DNI
- ✅ `PUT /api/v1/extension/solicitud/{dni}/estado` - Actualizar estado
- ✅ `PUT /api/v1/extension/solicitud/{dni}/enviada` - Marcar como enviada
- ✅ `PUT /api/v1/extension/traslado/{dni}/enviado` - Marcar traslado enviado
- ✅ `GET /api/v1/extension/traslado/{dni}/pdf` - Descargar PDF de traslado

#### 4. **Sistema de Email**
- ✅ Templates completos (user_credentials, status_update, confirmation, approved, rejected)
- ✅ Servicio de email integrado con Django
- ✅ Envío automático de emails al aprobar/rechazar solicitudes
- ✅ Tareas Celery para envío asíncrono

#### 5. **Configuración**
- ✅ JWT configurado (compatible con hps-system)
- ✅ Celery configurado con colas separadas
- ✅ Configuración de email unificada (SMTP/IMAP)
- ✅ Variables de entorno compatibles con ambos sistemas

#### 6. **Admin Django**
- ✅ Todos los modelos registrados en admin
- ✅ Filtros y búsquedas configurados
- ✅ Fieldsets organizados para HpsRequest

---

## Pasos para Iniciar Pruebas

### 1. **Preparar Base de Datos**

```bash
cd cryptotrace/cryptotrace-backend/src
python manage.py makemigrations hps_core
python manage.py migrate hps_core
```

### 2. **Crear Datos de Prueba**

#### Crear roles HPS:
```python
from hps_core.models import HpsRole

HpsRole.objects.create(name='admin', description='Administrador del sistema')
HpsRole.objects.create(name='team_lead', description='Líder de equipo')
HpsRole.objects.create(name='member', description='Miembro del equipo')
HpsRole.objects.create(name='crypto', description='Usuario CryptoTrace')
```

#### Crear un equipo:
```python
from hps_core.models import HpsTeam
from django.contrib.auth import get_user_model

User = get_user_model()
admin_user = User.objects.first()  # O crear uno específico

team = HpsTeam.objects.create(
    name='Equipo de Prueba',
    description='Equipo para testing',
    team_lead=admin_user
)
```

#### Crear perfil HPS para un usuario:
```python
from hps_core.models import HpsUserProfile, HpsRole

user = User.objects.first()
role = HpsRole.objects.get(name='admin')

profile = HpsUserProfile.objects.create(
    user=user,
    role=role,
    team=team
)
```

### 3. **Probar Endpoints**

#### Autenticación:
```bash
# Obtener token JWT
curl -X POST http://localhost:8080/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "tu_usuario", "password": "tu_password"}'
```

#### Listar solicitudes HPS:
```bash
curl -X GET http://localhost:8080/api/v1/hps/requests/ \
  -H "Authorization: Bearer TU_TOKEN_JWT"
```

#### Crear solicitud HPS:
```bash
curl -X POST http://localhost:8080/api/v1/hps/requests/ \
  -H "Authorization: Bearer TU_TOKEN_JWT" \
  -H "Content-Type: application/json" \
  -d '{
    "document_type": "DNI",
    "document_number": "12345678A",
    "birth_date": "1990-01-01",
    "first_name": "Juan",
    "first_last_name": "Pérez",
    "nationality": "Española",
    "birth_place": "Madrid",
    "email": "juan@example.com",
    "phone": "600123456",
    "request_type": "new",
    "status": "pending"
  }'
```

#### Probar endpoints de extensiones (sin autenticación):
```bash
# Listar personas pendientes
curl -X GET http://localhost:8080/api/v1/extension/personas

# Obtener persona por DNI
curl -X GET http://localhost:8080/api/v1/extension/persona/12345678A

# Marcar solicitud como enviada
curl -X PUT http://localhost:8080/api/v1/extension/solicitud/12345678A/enviada
```

### 4. **Probar Admin Django**

1. Acceder a `http://localhost:8080/admin/`
2. Iniciar sesión con usuario admin
3. Verificar que aparecen todos los modelos HPS:
   - Roles HPS
   - Equipos HPS
   - Membresías de equipo HPS
   - Perfiles de usuario HPS
   - Plantillas HPS
   - Solicitudes HPS
   - Tokens HPS
   - Logs de auditoría HPS

### 5. **Probar Funcionalidades Específicas**

#### Crear y usar token:
```python
from hps_core.models import HpsToken
from django.contrib.auth import get_user_model

User = get_user_model()
admin = User.objects.first()

# Crear token
token = HpsToken.create_token(
    email='nuevo@example.com',
    requested_by_user=admin,
    purpose='Solicitud de prueba',
    hours_valid=72
)

# Verificar token
print(f"Token: {token.token}")
print(f"Válido: {token.is_valid}")
print(f"Expirado: {token.is_expired}")
```

#### Aprobar solicitud (envía email automáticamente):
```python
from hps_core.models import HpsRequest
from hps_core.services import HpsRequestService
from django.contrib.auth import get_user_model
from datetime import date, timedelta

User = get_user_model()
admin = User.objects.first()
hps = HpsRequest.objects.first()

# Aprobar (envía email automáticamente)
HpsRequestService.approve(
    hps_request=hps,
    user=admin,
    expires_at=date.today() + timedelta(days=365),
    notes="Aprobado para pruebas"
)
```

---

## Checklist de Pruebas

### Funcionalidades Básicas
- [ ] Crear roles HPS desde admin
- [ ] Crear equipos HPS desde admin
- [ ] Asignar usuarios a equipos
- [ ] Crear solicitud HPS desde API
- [ ] Listar solicitudes HPS con filtros
- [ ] Aprobar solicitud HPS (verificar email)
- [ ] Rechazar solicitud HPS (verificar email)
- [ ] Crear token HPS
- [ ] Crear solicitud pública con token

### Endpoints de Extensiones
- [ ] Listar personas pendientes
- [ ] Obtener persona por DNI
- [ ] Actualizar estado de solicitud
- [ ] Marcar solicitud como enviada
- [ ] Descargar PDF de traslado (si existe)

### Integración
- [ ] Verificar que usuarios de CryptoTrace tienen perfil HPS automático
- [ ] Verificar que los emails se envían correctamente
- [ ] Verificar que Celery procesa las tareas
- [ ] Verificar logs de auditoría

### Permisos
- [ ] Admin puede ver todas las solicitudes
- [ ] Team Lead solo ve solicitudes de su equipo
- [ ] Member solo ve sus propias solicitudes
- [ ] Endpoints de extensiones son públicos (sin auth)

---

## Notas Importantes

1. **Migraciones**: Asegúrate de ejecutar las migraciones antes de probar
2. **Variables de Entorno**: Configura las variables de email si quieres probar el envío real
3. **Celery**: Si quieres probar tareas asíncronas, necesitas Redis y Celery worker corriendo
4. **Base de Datos**: Los modelos HPS se crean en la misma BD de CryptoTrace
5. **Autenticación**: Usa el mismo sistema JWT de CryptoTrace (SimpleJWT)

---

## Próximos Pasos (No Implementados Aún)

- [ ] Endpoints de chat/agente IA
- [ ] Procesamiento de correos entrantes (IMAP)
- [ ] Integración con agente IA
- [ ] WebSockets para chat en tiempo real
- [ ] Scripts de migración de datos desde FastAPI

---

**Estado**: ✅ Listo para pruebas básicas de funcionalidad HPS  
**Última actualización**: 2025-01-XX

