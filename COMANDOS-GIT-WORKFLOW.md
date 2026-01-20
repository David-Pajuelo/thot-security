# Comandos Git y Workflow Dev/Prod

## Workflow de Ramas

El proyecto usa dos ramas principales:
- **`development`**: Rama de desarrollo donde se hacen los cambios
- **`production`**: Rama de producción que se despliega en el VPS

## Comandos Git Básicos

### Trabajar en Desarrollo

```bash
# Asegurarse de estar en la rama development
git checkout development

# Actualizar desde remoto
git pull origin development

# Hacer cambios y commitear
git add .
git commit -m "Descripción del cambio"
git push origin development
```

### Mover Cambios a Producción

```bash
# Cambiar a producción
git checkout production

# Mergear development en production
git merge development

# Subir a producción
git push origin production

# Volver a development
git checkout development
```

### Actualizar VPS desde Producción

```bash
# En el VPS
cd /opt/thot-security

# Actualizar código
git pull origin production

# Reconstruir y reiniciar servicios según corresponda
# (ver INSTRUCCIONES-DESPLIEGUE-VPS.md)
```

## Resolver Conflictos

Si hay conflictos al hacer merge o pull:

```bash
# Ver qué archivos tienen conflictos
git status

# Ver las diferencias
git diff

# Opción 1: Guardar cambios locales temporalmente
git stash
git pull origin production
git stash pop

# Opción 2: Descartar cambios locales (¡CUIDADO!)
git reset --hard origin/production
git pull origin production
```

## Comandos Útiles

```bash
# Ver estado actual
git status

# Ver historial de commits
git log --oneline -10

# Ver diferencias entre ramas
git diff development..production

# Ver qué archivos cambiaron
git diff --name-only development..production
```
