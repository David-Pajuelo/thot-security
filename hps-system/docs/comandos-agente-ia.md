# 📋 Comandos del Agente IA - Estado Actual

## ✅ Comandos Implementados (Versión Actual)

### 🔍 Consultas HPS
1. **`estado hps de [email]`** o solo `[email]`
   - ✅ Implementado
   - Consulta el estado de HPS de un usuario
   - Funciona para todos los roles

2. **`hps de mi equipo`**
   - ✅ Implementado
   - Lista las HPS del equipo del usuario
   - Disponible para team_lead y admin

3. **`todas las hps`**
   - ✅ Implementado
   - Estadísticas globales de todas las HPS
   - Solo para admin

### 👥 Gestión de Usuarios y Equipos
4. **`listar usuarios`**
   - ✅ Implementado
   - Lista usuarios (todos para admin, solo del equipo para team_lead)
   - Disponible para admin, team_lead

5. **`listar equipos`**
   - ✅ Implementado
   - Lista todos los equipos del sistema
   - Disponible para todos los roles

### 📚 Ayuda
6. **`comandos disponibles`** o `ayuda`
   - ✅ Implementado
   - Muestra comandos disponibles según el rol
   - Disponible para todos

7. **`ayuda hps`**
   - ✅ Implementado
   - Información sobre qué es HPS
   - Disponible para todos

### 📧 Gestión de HPS - Solicitudes (Envío de Formularios)

**IMPORTANTE**: Ambos comandos son **solicitudes** que envían un correo con un formulario al usuario. La diferencia es el tipo de solicitud:

8. **`envío hps a [email]`** o **`solicitar hps para [email]`**
   - ✅ Implementado
   - **Tipo**: Solicitud de **NUEVA HPS**
   - **Acción**: Genera token HPS y envía email con formulario de nueva HPS
   - **Variaciones reconocidas**: "envío hps a", "enviar hps a", "envia hps a", "envio hps a", "solicitar hps para", "generar hps para"
   - **Disponible para**: admin, team_lead, jefe_seguridad, crypto

9. **`envío traspaso hps a [email]`** o **`trasladar hps de [email]`** o **`traspasar hps de [email]`**
   - ✅ Implementado
   - **Tipo**: Solicitud de **TRASPASO HPS**
   - **Acción**: Genera token HPS para traspaso y envía email con formulario de traspaso
   - **Variaciones reconocidas**: "envío traspaso hps a", "enviar traspaso hps a", "envia traspaso hps a", "envio traspaso hps a", "trasladar hps de", "traspasar hps de"
   - **Solo para**: admin, jefe_seguridad, jefe_seguridad_suplente

---

## ❌ Comandos Faltantes (Del Original FastAPI)

### 🔧 Gestión de Usuarios (Alta Prioridad)
1. **`crear usuario [email]`**
   - ❌ No implementado
   - Crear nuevo usuario en el sistema
   - Disponible para: admin, team_lead

2. **`dar alta jefe de equipo [nombre] [email] [equipo]`**
   - ❌ No implementado
   - Crear jefe de equipo con equipo asignado
   - Solo para admin

3. **`modificar rol de [email] a [rol]`**
   - ❌ No implementado
   - Cambiar rol de un usuario
   - Disponible para: admin, jefe_seguridad

### 👥 Gestión de Equipos (Media Prioridad)
4. **`crear equipo [nombre]`**
   - ❌ No implementado
   - Crear nuevo equipo
   - Solo para admin

5. **`asignar usuario [email] al equipo [nombre]`**
   - ❌ No implementado
   - Asignar usuario a un equipo
   - Disponible para: admin, team_lead

### 📋 Gestión de HPS (Alta Prioridad)
6. **`renovar hps de [email]`**
   - ❌ No implementado
   - Iniciar proceso de renovación de HPS
   - Disponible para: admin, team_lead, jefe_seguridad

7. **`trasladar hps de [email]`** o **`traspasar hps de [email]`**
   - ❌ No implementado
   - Iniciar proceso de traspaso HPS
   - Solo para: admin, jefe_seguridad, jefe_seguridad_suplente

8. **`aprobar hps de [email]`**
   - ❌ No implementado (removido del original, se maneja desde extensión)
   - Aprobar solicitud HPS
   - Disponible para: admin, team_lead, crypto

9. **`rechazar hps de [email]`**
   - ❌ No implementado (removido del original, se maneja desde extensión)
   - Rechazar solicitud HPS
   - Disponible para: admin, team_lead, crypto

### 📊 Consultas Adicionales (Baja Prioridad)
10. **`mi historial hps`**
    - ❌ No implementado
    - Ver historial de HPS del usuario
    - Disponible para: todos

11. **`cuando expira mi hps`**
    - ❌ No implementado
    - Ver fecha de vencimiento de HPS
    - Disponible para: todos

12. **`estado de mi equipo`**
    - ❌ No implementado
    - Ver estado general del equipo
    - Disponible para: team_lead, admin

---

## 📊 Resumen

### Estadísticas
- **Total comandos en original**: ~18 comandos
- **Comandos implementados**: 9 comandos (50%)
- **Comandos parcialmente implementados**: 0 comandos (0%)
- **Comandos faltantes**: 9 comandos (50%)

### Por Categoría
- **Consultas HPS**: 3/4 implementados (75%)
- **Gestión Usuarios**: 1/4 implementados (25%)
- **Gestión Equipos**: 1/3 implementados (33%)
- **Gestión HPS (Envío formularios)**: 2/2 implementados (100%) ✅
- **Gestión HPS (Otros)**: 0/2 implementados (0%) - renovar, aprobar/rechazar
- **Ayuda**: 2/2 implementados (100%)

---

## 🎯 Recomendación de Prioridad para Expansión

### 🔴 Alta Prioridad (Funcionalidad Core)
1. ✅ **`envío hps a [email]`** (Solicitud de NUEVA HPS) - ✅ IMPLEMENTADO
   - Genera token y envía email con formulario de nueva HPS
   - Funcional y probado
   - Variaciones: "envío hps a", "solicitar hps para", etc.

2. ✅ **`envío traspaso hps a [email]`** (Solicitud de TRASPASO HPS) - ✅ IMPLEMENTADO
   - Genera token para traspaso y envía email con formulario de traspaso
   - Funcional y probado
   - Variaciones: "envío traspaso hps a", "trasladar hps de", "traspasar hps de", etc.

3. **`renovar hps de [email]`**
   - Funcionalidad muy usada
   - Similar a solicitar HPS

4. **`crear usuario [email]`**
   - Funcionalidad básica de gestión
   - Requiere integración con servicios de usuario

### 🟡 Media Prioridad (Gestión)
5. **`modificar rol de [email] a [rol]`**
   - Útil para administración
   - Requiere validación de permisos

6. **`crear equipo [nombre]`**
   - Útil para organización
   - Solo para admin

7. **`asignar usuario [email] al equipo [nombre]`**
   - Útil para gestión de equipos
   - Requiere validación de permisos

8. **`dar alta jefe de equipo [nombre] [email] [equipo]`**
   - Funcionalidad específica
   - Requiere creación de usuario + asignación de rol + equipo

### 🟢 Baja Prioridad (Consultas Adicionales)
9. **`mi historial hps`**
   - Consulta informativa
   - No crítica para funcionamiento

10. **`cuando expira mi hps`**
    - Consulta informativa
    - Puede incluirse en estado HPS

11. **`estado de mi equipo`**
    - Consulta informativa
    - Puede combinarse con "hps de mi equipo"

---

## 💡 Notas

- Los comandos de **aprobar/rechazar HPS** fueron removidos del original porque se manejan desde la extensión de navegador
- El comando **`solicitar hps`** está parcialmente implementado pero necesita integración con el servicio de tokens
- La mayoría de comandos faltantes requieren integración con servicios Django existentes (`HpsTokenService`, servicios de usuario, etc.)

---

**Última actualización**: 2025-12-04

