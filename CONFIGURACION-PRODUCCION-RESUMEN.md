# 🔐 Configuración de Producción - Resumen

Este documento contiene todas las credenciales y configuraciones necesarias para el despliegue en producción.

## 📌 Información del VPS

- **IP:** `46.183.119.90`
- **DNS:** `071fb23c-d520-4dbd-9664-ca358dd46e9e.clouding.host`
- **Usuario:** `root`
- **Contraseña:** `XJrdNfXBm2k-7HG`
- **Dominio:** `seguridad.idiaicox.com` (para ambas aplicaciones)

---

## 🔑 Credenciales Generadas

### Base de Datos CryptoTrace
- **Nombre BD:** `cryptotrace_prod`
- **Usuario:** `cryptotrace_user`
- **Contraseña:** `SAmSPFVFKvlYZn_Z2Z1SGzwHdRs2WNW88FsuOZ-33eI`

### Base de Datos HPS System
- **Nombre BD:** `hps_system`
- **Usuario:** `hps_user`
- **Contraseña:** `Vd3GNWIEzha4-vb63mWvPhb612hKWRMFEKzh0bJonnQ`

### Django SECRET_KEY
- **SECRET_KEY:** `qpfOHYiJSQ_09OJsV1Nl3hhRRvgx2nODjETUlxQFAcUCUtfg-j6EwSnwUi1fFVYZeFE`

### JWT SECRET_KEY
- **JWT_SECRET_KEY (CryptoTrace):** `As_t7LfbpA_8cru4V2vZFteP1VVFf_GsaiW_Uj4tuhVpCtsjab9cSleN92w1C3EuyVE`
- **JWT_SECRET_KEY (HPS System):** `As_t7LfbpA_8cru4V2vZFteP1VVFf_GsaiW_Uj4tuhVpCtsjab9cSleN92w1C3EuyVE` (puede ser diferente)

---

## 📝 Variables de Entorno - CryptoTrace Backend

**Archivo:** `/opt/thot-security/cryptotrace/cryptotrace-backend/.env.prod`

```bash
# BASE DE DATOS
DATABASE_URL=postgres://cryptotrace_user:SAmSPFVFKvlYZn_Z2Z1SGzwHdRs2WNW88FsuOZ-33eI@db:5432/cryptotrace_prod
DB_NAME=cryptotrace_prod
DB_USER=cryptotrace_user
DB_PASSWORD=SAmSPFVFKvlYZn_Z2Z1SGzwHdRs2WNW88FsuOZ-33eI
DB_HOST=db
DB_PORT=5432

# SECRET KEYS
SECRET_KEY=qpfOHYiJSQ_09OJsV1Nl3hhRRvgx2nODjETUlxQFAcUCUtfg-j6EwSnwUi1fFVYZeFE
JWT_SECRET_KEY=As_t7LfbpA_8cru4V2vZFteP1VVFf_GsaiW_Uj4tuhVpCtsjab9cSleN92w1C3EuyVE

# FRONTEND
FRONTEND_URL=https://seguridad.idiaicox.com
HPS_SYSTEM_URL=https://seguridad.idiaicox.com
NEXT_PUBLIC_HPS_SYSTEM_URL=https://seguridad.idiaicox.com

# CORS
CORS_ALLOWED_ORIGINS=https://seguridad.idiaicox.com,https://www.seguridad.idiaicox.com
CORS_ALLOW_ALL_ORIGINS=False

# DJANGO
DEBUG=False
ENVIRONMENT=production
DJANGO_SETTINGS_MODULE=cryptotrace_backend.settings_prod
ALLOWED_HOSTS=seguridad.idiaicox.com,www.seguridad.idiaicox.com,46.183.119.90

# REDIS
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
CELERY_TIMEZONE=UTC

# OPENAI
OPENAI_API_KEY=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
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_TOKENS=2000
OPENAI_TEMPERATURE=0.7

# EMAIL SMTP/IMAP
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=aicoxidi@gmail.com
SMTP_PASSWORD=wxnopfgcliyexyqf
SMTP_USE_TLS=true
SMTP_FROM_EMAIL=noreply@seguridad.idiaicox.com
SMTP_FROM_NAME=Sistema HPS
SMTP_REPLY_TO=aicoxidi@gmail.com

IMAP_HOST=imap.gmail.com
IMAP_PORT=993
IMAP_USER=aicoxidi@gmail.com
IMAP_PASSWORD=wxnopfgcliyexyqf
IMAP_MAILBOX=INBOX
```

---

## 📝 Variables de Entorno - HPS System

**Archivo:** `/opt/thot-security/hps-system/.env.prod`

```bash
# BASE DE DATOS
POSTGRES_DB=hps_system
POSTGRES_USER=hps_user
POSTGRES_PASSWORD=Vd3GNWIEzha4-vb63mWvPhb612hKWRMFEKzh0bJonnQ
POSTGRES_HOST=db
POSTGRES_PORT=5432

# JWT
JWT_SECRET_KEY=As_t7LfbpA_8cru4V2vZFteP1VVFf_GsaiW_Uj4tuhVpCtsjab9cSleN92w1C3EuyVE
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=480
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# FRONTEND
REACT_APP_API_URL=https://seguridad.idiaicox.com
REACT_APP_WS_URL=wss://seguridad.idiaicox.com
REACT_APP_AGENTE_IA_WS_URL=wss://seguridad.idiaicox.com/agente-ia/
REACT_APP_ENVIRONMENT=production
REACT_APP_VERSION=0.1.0
FRONTEND_URL=https://seguridad.idiaicox.com

# BACKEND
BACKEND_HOST=backend
BACKEND_PORT=8001
BACKEND_WORKERS=1
BACKEND_RELOAD=false
BACKEND_URL=http://backend:8001

# REDIS
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# OPENAI
OPENAI_API_KEY=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
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_TOKENS=2000
OPENAI_TEMPERATURE=0.7

# EMAIL SMTP/IMAP
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=aicoxidi@gmail.com
SMTP_PASSWORD=wxnopfgcliyexyqf
SMTP_FROM_NAME=HPS System
SMTP_REPLY_TO=aicoxidi@gmail.com

IMAP_HOST=imap.gmail.com
IMAP_PORT=993
IMAP_USER=aicoxidi@gmail.com
IMAP_PASSWORD=wxnopfgcliyexyqf
IMAP_MAILBOX=INBOX

# SEGURIDAD
CORS_ORIGINS=https://seguridad.idiaicox.com
SECRET_KEY=As_t7LfbpA_8cru4V2vZFteP1VVFf_GsaiW_Uj4tuhVpCtsjab9cSleN92w1C3EuyVE
ENVIRONMENT=production
```

---

## ✅ Configuración Completa

Todas las credenciales necesarias están configuradas:
- ✅ OpenAI API Key configurada
- ✅ Credenciales de Email (Gmail) configuradas
- ✅ Contraseñas de base de datos generadas
- ✅ Secret Keys generadas

**Nota:** Las credenciales de email y OpenAI son las mismas que en desarrollo, lo cual es válido para empezar. Se recomienda crear credenciales separadas para producción en el futuro.

---

## 🔒 Seguridad

**IMPORTANTE:**
- Este archivo contiene información sensible
- No subir a Git
- Mantener en lugar seguro
- Cambiar todas las contraseñas después del primer despliegue si es necesario
- Usar contraseñas diferentes para cada entorno (desarrollo/producción)

---

**Última actualización:** 2025-01-27

