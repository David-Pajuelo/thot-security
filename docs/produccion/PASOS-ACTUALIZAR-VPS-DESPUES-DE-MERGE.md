# Pasos para actualizar la VPS tras merge a production

**Cuándo usar:** Después de hacer `git merge development` en `production` y `git push origin production`. Ejecutar **en la VPS** (SSH).

---

## 1. Conectar y actualizar código

```bash
ssh root@187.33.154.156
# (o el usuario que uses)

cd /opt/thot-security
git checkout production
git pull origin production
```

---

## 2. CryptoTrace: migraciones y rebuild

```bash
cd /opt/thot-security/cryptotrace

# Migraciones (obligatorio: incluye 0009 UserAccessLog, 0010 remove_useraccesslog, monitorizacion, etc.)
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate

# Reconstruir y levantar todos los servicios (backend, frontend, processing, ocr, celery, pdf-generator)
docker compose -f docker-compose.prod.yml up -d --build

# Archivos estáticos (si cambió frontend CryptoTrace)
docker compose -f docker-compose.prod.yml exec backend python manage.py collectstatic --noinput
```

---

## 3. HPS System: frontend

```bash
cd /opt/thot-security/hps-system
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build frontend
```

---

## 4. Comprobar

```bash
# CryptoTrace
cd /opt/thot-security/cryptotrace
docker compose -f docker-compose.prod.yml ps

# HPS
cd /opt/thot-security/hps-system
docker compose -f docker-compose.prod.yml ps
```

Probar en el navegador: https://seguridad.idiaicox.com (login, chat IA, monitorización).

---

**Referencia:** [CHECKLIST-ACTUALIZACION-VPS.md](CHECKLIST-ACTUALIZACION-VPS.md), [GUIA-DESPLIEGUE-PRODUCCION-VPS.md](GUIA-DESPLIEGUE-PRODUCCION-VPS.md).
