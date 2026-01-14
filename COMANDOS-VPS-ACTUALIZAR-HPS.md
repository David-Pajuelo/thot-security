# Comandos para actualizar HPS System en VPS

## Pasos para aplicar el fix de UserManagement.jsx

```bash
# 1. Ir al directorio del proyecto
cd /opt/thot-security

# 2. Hacer pull de la rama production
git pull origin production

# 3. Ir al directorio de HPS System
cd hps-system

# 4. Reconstruir el frontend (ya que cambiamos código React)
docker compose -f docker-compose.prod.yml --env-file .env.prod build frontend

# 5. Reiniciar el contenedor del frontend
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d frontend

# 6. Verificar que el contenedor está corriendo
docker compose -f docker-compose.prod.yml --env-file .env.prod ps frontend

# 7. Ver logs para verificar que todo está bien
docker compose -f docker-compose.prod.yml --env-file .env.prod logs -f frontend
```

## Comandos en una sola línea (opcional)

```bash
cd /opt/thot-security && git pull origin production && cd hps-system && docker compose -f docker-compose.prod.yml --env-file .env.prod build frontend && docker compose -f docker-compose.prod.yml --env-file .env.prod up -d frontend
```

