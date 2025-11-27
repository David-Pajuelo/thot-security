# Workflow Git para Producción (VPS)

Este documento explica cómo gestionar los cambios específicos del VPS usando una rama separada de producción.

## Estructura de Ramas

- **`desarrollo-pajuelo`**: Rama principal de desarrollo (local)
- **`produccion`**: Rama específica para el VPS en producción

## Configuración Inicial en el VPS

```bash
cd /opt/hps-system

# Cambiar a la rama de producción
git checkout produccion

# Si la rama no existe localmente, crearla desde remoto
git fetch origin
git checkout -b produccion origin/produccion
```

## Workflow de Trabajo

### 1. Hacer Cambios en Desarrollo (Local)

```bash
# Trabajar en desarrollo-pajuelo
git checkout desarrollo-pajuelo

# Hacer cambios y commits
git add .
git commit -m "Descripción del cambio"
git push origin desarrollo-pajuelo
```

### 2. Aplicar Cambios Generales a Producción

Si un cambio de desarrollo también debe aplicarse en producción:

```bash
# Desde desarrollo-pajuelo
git checkout produccion
git merge desarrollo-pajuelo

# Resolver conflictos si los hay (el .env y configuraciones específicas del VPS)
# Luego hacer push
git push origin produccion
```

### 3. Hacer Cambios Específicos de Producción

Si necesitas hacer cambios que solo aplican al VPS:

```bash
# En el VPS
cd /opt/hps-system
git checkout produccion
git pull origin produccion

# Hacer los cambios necesarios (ej: ajustar docker-compose.yml, .env, etc.)
# Luego hacer commit y push
git add .
git commit -m "Cambio específico para producción"
git push origin produccion
```

### 4. Actualizar VPS desde Producción

Cuando hay cambios en la rama `produccion`:

```bash
# En el VPS
cd /opt/hps-system
git pull origin produccion

# Reconstruir servicios si es necesario
docker compose down
docker compose build --no-cache
docker compose up -d
```

## Ejemplos de Cambios Específicos de Producción

### Cambios que van SOLO a producción:
- Configuraciones específicas del VPS (IPs, dominios, SSL)
- Valores por defecto en docker-compose.yml para producción
- Scripts de deployment específicos
- Configuraciones de Nginx para producción
- Variables de entorno específicas del servidor

### Cambios que van a AMBAS ramas:
- Nuevas funcionalidades
- Correcciones de bugs
- Mejoras generales
- Cambios en el código de la aplicación

## Mejores Prácticas

1. **Nunca hardcodear valores de producción en `desarrollo-pajuelo`**
   - Usar siempre variables de entorno
   - Cada ambiente tiene su propio `.env`

2. **Mantener `.env` fuera de git**
   - El `.env` está en `.gitignore`
   - Usar `.env.example` como template

3. **Documentar cambios específicos de producción**
   - Si haces un cambio solo para producción, documentarlo
   - Comentarios claros en los commits

4. **Sincronizar cambios importantes**
   - Si un cambio en producción es útil también en desarrollo, hacer merge
   - Ejemplo: mejoras en docker-compose.yml que benefician ambos ambientes

## Troubleshooting

### Si hay conflictos al hacer merge de desarrollo-pajuelo a produccion:

```bash
git checkout produccion
git merge desarrollo-pajuelo

# Resolver conflictos manualmente
# Generalmente en .env o docker-compose.yml

git add .
git commit -m "Merge desarrollo-pajuelo: resolver conflictos"
git push origin produccion
```

### Si necesitas revertir un cambio en producción:

```bash
# En el VPS
git checkout produccion
git log  # Ver commits
git revert <commit-hash>
git push origin produccion

# Reconstruir servicios
docker compose down
docker compose build --no-cache
docker compose up -d
```

## Comandos Rápidos de Referencia

```bash
# Ver rama actual
git branch

# Ver estado
git status

# Actualizar rama de producción
git checkout produccion
git pull origin produccion

# Ver diferencias entre ramas
git diff desarrollo-pajuelo..produccion

# Ver qué archivos difieren
git diff --name-only desarrollo-pajuelo..produccion
```

