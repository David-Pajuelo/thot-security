# Resolver conflicto en VPS antes de actualizar

## Problema
El pull está bloqueado por cambios locales en `hps-system/docker-compose-prod.sh`

## Solución 1: Guardar cambios temporalmente (recomendado)

```bash
# Ver qué cambios hay localmente
git status

# Ver las diferencias (opcional, para verificar qué se perderá)
git diff hps-system/docker-compose-prod.sh

# Guardar los cambios temporalmente
git stash

# Ahora hacer el pull
git pull origin production

# Si necesitas recuperar los cambios después:
# git stash pop
```

## Solución 2: Descartar cambios locales (si no son importantes)

```bash
# Ver qué cambios hay
git diff hps-system/docker-compose-prod.sh

# Descartar los cambios locales
git checkout -- hps-system/docker-compose-prod.sh

# Ahora hacer el pull
git pull origin production
```

## Solución 3: Hacer commit de los cambios locales (si son importantes)

```bash
# Ver qué cambios hay
git diff hps-system/docker-compose-prod.sh

# Si los cambios son importantes, hacer commit
git add hps-system/docker-compose-prod.sh
git commit -m "Cambios locales en docker-compose-prod.sh"

# Ahora hacer el pull (puede haber conflictos que resolver)
git pull origin production
```

## Después de resolver el conflicto

Una vez resuelto, continúa con la actualización:

```bash
cd cryptotrace
docker compose -f docker-compose.prod.yml build --no-cache ocr frontend
docker compose -f docker-compose.prod.yml up -d ocr frontend
```

