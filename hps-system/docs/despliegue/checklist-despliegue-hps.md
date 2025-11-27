# ✅ Checklist de Despliegue - hps.aicoxidi.com

## 📋 Información del Servidor

- **IP**: 46.183.119.90
- **Dominio**: hps.aicoxidi.com
- **Usuario**: root
- **DNS**: 071fb23c-d520-4dbd-9664-ca358dd46e9e.clouding.host

---

## 🔐 Paso 1: Conectar a la VPS

```bash
# Conectar por SSH
ssh root@46.183.119.90

# O usando el dominio (una vez configurado DNS)
ssh root@hps.aicoxidi.com
```

**Contraseña**: XJrdNfXBm2k-7HG

✅ **Verificar**: ¿Puedes conectarte? Si no, verifica que el puerto 22 esté abierto.

---

## 🖥️ Paso 2: Verificar Sistema Operativo

```bash
# Ver información del sistema
cat /etc/os-release
uname -a
```

✅ **Verificar**: ¿Qué distribución de Linux es? (Ubuntu/Debian/CentOS)

---

## 📦 Paso 3: Preparar el Sistema

```bash
# Actualizar sistema
apt update && apt upgrade -y

# Instalar herramientas básicas
apt install -y git curl wget nano ufw

# Verificar versión de Python (necesario para algunas herramientas)
python3 --version
```

✅ **Verificar**: ¿Se instalaron correctamente las herramientas?

---

## 🔥 Paso 4: Configurar Firewall

```bash
# Habilitar firewall
ufw --force enable

# Permitir puertos necesarios
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp  # HTTPS

# Ver estado
ufw status
```

✅ **Verificar**: ¿El firewall está activo y muestra los puertos permitidos?

---

## 🐳 Paso 5: Instalar Docker

```bash
# Instalar dependencias
apt install -y apt-transport-https ca-certificates curl gnupg lsb-release

# Agregar clave GPG de Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Agregar repositorio (ajustar según tu distribución)
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

# Instalar Docker
apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Verificar instalación
docker --version
docker compose version
```

✅ **Verificar**: ¿Docker y Docker Compose están instalados?

---

## 📥 Paso 6: Clonar Repositorio

```bash
# Crear directorio y clonar
mkdir -p /opt/hps-system
cd /opt
git clone https://github.com/calonsoaicox/hps-system.git hps-system
cd hps-system

# Verificar que se clonó correctamente
ls -la
```

✅ **Verificar**: ¿Se clonó el repositorio correctamente?

---

## ⚙️ Paso 7: Configurar Variables de Entorno

```bash
# Copiar archivo de ejemplo
cp env.example .env

# Editar con tus credenciales
nano .env
```

**Variables importantes a configurar:**

```bash
# Base de datos
POSTGRES_PASSWORD=GENERAR_PASSWORD_SEGURO_AQUI

# JWT
JWT_SECRET_KEY=GENERAR_CLAVE_SECRETA_AQUI

# Email (Private Mail)
SMTP_HOST=mail.privateemail.com
SMTP_USER=seguridad@idiaicox.com
SMTP_PASSWORD=TU_PASSWORD_EMAIL
IMAP_USER=seguridad@idiaicox.com
IMAP_PASSWORD=TU_PASSWORD_EMAIL

# Frontend (URLs de producción)
REACT_APP_API_URL=https://hps.aicoxidi.com/api
REACT_APP_WS_URL=wss://hps.aicoxidi.com/api
REACT_APP_AGENTE_IA_WS_URL=wss://hps.aicoxidi.com/agente-ia

# Entorno
ENVIRONMENT=production
DEBUG=false
```

**Generar claves seguras:**
```bash
# Generar JWT_SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Generar POSTGRES_PASSWORD
python3 -c "import secrets; print(secrets.token_urlsafe(24))"
```

✅ **Verificar**: ¿Todas las variables están configuradas correctamente?

---

## 🚀 Paso 8: Construir y Levantar Servicios

```bash
# Construir imágenes
docker compose build

# Levantar servicios
docker compose up -d

# Ver estado
docker compose ps

# Ver logs
docker compose logs -f
```

✅ **Verificar**: ¿Todos los servicios están "Up" y "healthy"?

---

## 🌐 Paso 9: Configurar DNS

En el panel de Clouding.host, configura el DNS:

- **Tipo**: A
- **Nombre**: hps (o @ para dominio raíz)
- **Valor**: 46.183.119.90
- **TTL**: 3600

O si prefieres usar el DNS proporcionado:
- Usa el DNS: 071fb23c-d520-4dbd-9664-ca358dd46e9e.clouding.host

✅ **Verificar**: ¿El DNS apunta correctamente? (puede tardar unos minutos)
```bash
# Verificar desde tu máquina local
nslookup hps.aicoxidi.com
```

---

## 🔒 Paso 10: Configurar Nginx

```bash
# Crear configuración
nano /etc/nginx/sites-available/hps-system
```

**Pegar el contenido del archivo de configuración que se creará a continuación**

```bash
# Habilitar sitio
ln -s /etc/nginx/sites-available/hps-system /etc/nginx/sites-enabled/
rm /etc/nginx/sites-enabled/default

# Verificar configuración
nginx -t

# Recargar Nginx
systemctl reload nginx
```

✅ **Verificar**: ¿Nginx está corriendo sin errores?

---

## 🔐 Paso 11: Obtener Certificado SSL

```bash
# Obtener certificado
certbot --nginx -d hps.aicoxidi.com

# Seguir instrucciones interactivas
# Email: tu-email@example.com
# Aceptar términos
# Redirigir HTTP a HTTPS: Yes
```

✅ **Verificar**: ¿El certificado SSL está instalado?
```bash
# Verificar certificado
certbot certificates
```

---

## ✅ Paso 12: Verificación Final

```bash
# Verificar servicios
docker compose ps

# Verificar logs
docker compose logs --tail=50

# Probar acceso desde navegador
# https://hps.aicoxidi.com
```

✅ **Verificar**: 
- [ ] ¿Puedes acceder a https://hps.aicoxidi.com?
- [ ] ¿La página carga correctamente?
- [ ] ¿El SSL funciona (candado verde)?
- [ ] ¿Puedes hacer login?
- [ ] ¿La API responde?

---

## 📝 Notas Importantes

1. **Backups**: Configurar backups automáticos después del despliegue
2. **Monitoreo**: Revisar logs regularmente
3. **Actualizaciones**: Mantener el sistema actualizado
4. **Seguridad**: Cambiar contraseñas por defecto

---

## 🆘 Si Algo Sale Mal

```bash
# Ver logs de errores
docker compose logs | grep -i error

# Reiniciar servicios
docker compose restart

# Ver estado de contenedores
docker ps -a

# Verificar espacio en disco
df -h
```

