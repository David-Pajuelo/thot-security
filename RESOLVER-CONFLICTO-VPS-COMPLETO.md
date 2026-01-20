# Resolver conflicto en VPS - Solución Completa

## Situación
- Muchos archivos `__pycache__` eliminados (no deberían estar en git)
- Archivo `docker-compose-prod.sh` modificado (fue eliminado en el merge)
- Archivos sin seguimiento: `FETCH_HEAD` y `.backup`

## Solución: Descartar todos los cambios locales

Ejecuta estos comandos en la VPS:

```bash
# Descartar todos los cambios locales (incluyendo eliminaciones)
git reset --hard HEAD

# Limpiar archivos sin seguimiento (opcional, pero recomendado)
git clean -fd

# Ahora hacer el pull
git pull origin production
```

## Explicación

- `git reset --hard HEAD`: Descarta todos los cambios locales y vuelve al estado del último commit
- `git clean -fd`: Elimina archivos y directorios sin seguimiento (como `FETCH_HEAD` y `.backup`)
- `git pull origin production`: Ahora debería funcionar sin problemas

## Después del pull

Continúa con la actualización de los servicios:

```bash
cd cryptotrace
docker compose -f docker-compose.prod.yml build --no-cache ocr frontend
docker compose -f docker-compose.prod.yml up -d ocr frontend
```

## Nota sobre __pycache__

Los archivos `__pycache__` son archivos compilados de Python que se generan automáticamente. No deberían estar en el repositorio git. Si quieres evitar este problema en el futuro, asegúrate de que `.gitignore` incluya:

```
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
```

