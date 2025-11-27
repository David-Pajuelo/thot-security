# 🚀 Guía de Despliegue en Producción - CryptoTrace

Esta guía te llevará paso a paso para desplegar CryptoTrace en un VPS de producción con SSL, proxy reverso y configuraciones de seguridad.

## 📋 Requisitos Previos

### VPS Requerimientos Mínimos
- **RAM:** 4GB mínimo (8GB recomendado)
- **CPU:** 2 cores mínimo (4 cores recomendado)
- **Almacenamiento:** 50GB mínimo (SSD recomendado)
- **SO:** Ubuntu 20.04+ / Debian 11+ / CentOS 8+

### Servicios Externos
- **Dominio:** Tu dominio apuntando a la IP del VPS
- **Email SMTP:** Para notificaciones (Gmail, etc.)

## 🔧 Preparación del VPS

### 1. Actualizar el sistema
```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Instalar Docker y Docker Compose
```bash
# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Añadir usuario al grupo docker
sudo usermod -aG docker $USER

# Instalar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Reiniciar sesión para aplicar cambios de grupo
exit
```

### 3. Configurar firewall (UFW)
```bash
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
```

## 📁 Preparación del Proyecto

### 1. Clonar el repositorio
```bash
cd /opt
sudo git clone https://github.com/tu-usuario/cryptotrace.git
sudo chown -R $USER:$USER cryptotrace
cd cryptotrace
```

### 2. Configurar variables de entorno
```bash
# Copiar archivo de ejemplo
cp cryptotrace-backend/env.prod.example cryptotrace-backend/.env.prod

# Editar configuraciones
nano cryptotrace-backend/.env.prod
```

**Configuraciones importantes a cambiar:**
```bash
# Seguridad
SECRET_KEY=TU_CLAVE_SECRETA_MUY_LARGA_Y_ALEATORIA
DEBUG=False
ALLOWED_HOSTS=tu-dominio.com,www.tu-dominio.com

# Base de datos
DB_PASSWORD=TU_PASSWORD_SEGURO_BD

# Email
EMAIL_HOST_USER=tu_email@gmail.com
EMAIL_HOST_PASSWORD=tu_contraseña_aplicacion

# URLs
FRONTEND_URL=https://tu-dominio.com
CORS_ALLOWED_ORIGINS=https://tu-dominio.com,https://www.tu-dominio.com
```

### 3. Configurar dominio en archivos
```bash
# Establecer variable de entorno con tu dominio
export DOMAIN_NAME=tu-dominio.com

# O editar manualmente los archivos:
# - docker-compose.prod.yml
# - nginx/conf.d/cryptotrace.conf
# - cryptotrace-backend/.env.prod
```

### 4. Dar permisos de ejecución a scripts
```bash
chmod +x scripts/deploy.sh
chmod +x scripts/setup-letsencrypt.sh
```

## 🚀 Despliegue

### 1. Primer despliegue
```bash
# Despliegue completo con certificados temporales
DOMAIN_NAME=tu-dominio.com ./scripts/deploy.sh

# O si ya configuraste la variable:
./scripts/deploy.sh
```

El script realizará:
- ✅ Verificación de dependencias
- ✅ Configuración de variables de entorno
- ✅ Creación de directorios necesarios
- ✅ Generación de certificados SSL temporales
- ✅ Backup de base de datos (si existe)
- ✅ Construcción y despliegue de contenedores
- ✅ Migración de base de datos
- ✅ Recolección de archivos estáticos
- ✅ Verificación de servicios

### 2. Configurar SSL real con Let's Encrypt
```bash
# Después de que la aplicación esté funcionando con certificados temporales
DOMAIN_NAME=tu-dominio.com EMAIL=admin@tu-dominio.com ./scripts/setup-letsencrypt.sh
```

### 3. Configurar renovación automática de SSL
```bash
# Añadir a crontab para renovación automática cada día a las 3 AM
crontab -e

# Añadir esta línea:
0 3 * * * /opt/cryptotrace/scripts/renew-ssl.sh
```

## 📊 Verificación del Despliegue

### Comprobar servicios
```bash
./scripts/deploy.sh check
```

### Ver logs
```bash
./scripts/deploy.sh logs

# O logs específicos:
docker-compose -f docker-compose.prod.yml logs -f nginx
docker-compose -f docker-compose.prod.yml logs -f backend
```

### Verificar conectividad
```bash
# Health check
curl https://tu-dominio.com/health

# API
curl https://tu-dominio.com/api/

# Frontend
curl -I https://tu-dominio.com/
```

## 🔧 Comandos de Mantenimiento

### Backup de base de datos
```bash
./scripts/deploy.sh backup
```

### Actualizar aplicación
```bash
# Hacer pull de cambios
git pull origin main

# Redesplegar
./scripts/deploy.sh
```

### Reiniciar servicios específicos
```bash
# Reiniciar solo backend
docker-compose -f docker-compose.prod.yml restart backend

# Reiniciar frontend
docker-compose -f docker-compose.prod.yml restart frontend
```

### Limpiar recursos no utilizados
```bash
# Limpiar imágenes huérfanas
docker system prune -f

# Limpiar volúmenes no utilizados
docker volume prune -f
```

## 🛡️ Configuraciones de Seguridad

### Configuraciones implementadas:
- ✅ SSL/TLS con Let's Encrypt
- ✅ Proxy reverso con Nginx
- ✅ Headers de seguridad HTTP
- ✅ Rate limiting en API
- ✅ Firewall configurado
- ✅ Contenedores con usuarios no-root
- ✅ Redes Docker aisladas
- ✅ Variables de entorno seguras

### Recomendaciones adicionales:
- Configurar fail2ban para protección contra ataques de fuerza bruta
- Usar claves SSH en lugar de contraseñas
- Configurar monitorización con herramientas como Grafana/Prometheus
- Realizar backups automáticos regulares

## 📁 Estructura de Archivos en Producción

```
/opt/cryptotrace/
├── docker-compose.prod.yml       # Configuración Docker para producción
├── nginx/                        # Configuración Nginx
│   ├── nginx.conf
│   ├── conf.d/cryptotrace.conf
│   └── ssl/                      # Certificados SSL
├── scripts/                      # Scripts de despliegue y mantenimiento
│   ├── deploy.sh
│   ├── setup-letsencrypt.sh
│   └── renew-ssl.sh
├── postgres-backup/              # Backups de base de datos
├── cryptotrace-backend/.env.prod # Variables de entorno de producción
└── logs/                         # Logs de aplicación
```

## 🚨 Solución de Problemas

### Los servicios no inician
```bash
# Verificar logs
docker-compose -f docker-compose.prod.yml logs

# Verificar configuración
docker-compose -f docker-compose.prod.yml config
```

### Problemas con SSL
```bash
# Verificar certificados
openssl x509 -in nginx/ssl/fullchain.pem -text -noout

# Regenerar certificados
rm nginx/ssl/*.pem
./scripts/setup-letsencrypt.sh
```

### Problemas de conectividad
```bash
# Verificar puertos
netstat -tulpn | grep -E '(80|443)'

# Verificar DNS
nslookup tu-dominio.com
```

### Base de datos no conecta
```bash
# Verificar logs de PostgreSQL
docker-compose -f docker-compose.prod.yml logs db

# Conectar manualmente a la BD
docker-compose -f docker-compose.prod.yml exec db psql -U postgres -d cryptotrace_prod
```

## 📞 Soporte

Si encuentras problemas durante el despliegue:

1. Revisa los logs: `./scripts/deploy.sh logs`
2. Verifica el estado: `./scripts/deploy.sh check`
3. Consulta esta documentación
4. Contacta al equipo de desarrollo

---

## 🎉 ¡Felicidades!

Tu aplicación CryptoTrace está ahora funcionando en producción con:
- 🔒 SSL/HTTPS habilitado
- 🚀 Proxy reverso optimizado
- 🛡️ Configuraciones de seguridad
- 📊 Monitorización básica
- 🔄 Backups automáticos

**URL de acceso:** https://tu-dominio.com 