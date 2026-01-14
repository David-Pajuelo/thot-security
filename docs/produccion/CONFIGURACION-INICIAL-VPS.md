# 🔧 Configuración Inicial del VPS

Esta guía te ayudará a configurar el VPS desde cero antes de desplegar las aplicaciones.

## 📌 Información del VPS

- **IP:** `187.33.154.156`
- **Usuario:** `root`
- **Contraseña:** `41c0x1d1!`
- **Dominio:** `seguridad.idiaicox.com`

---

## 🔐 Paso 1: Conectar al VPS

```bash
ssh root@187.33.154.156
```

Cuando te pida la contraseña, introduce: `41c0x1d1!`

---

## 📋 Paso 2: Verificar Sistema Operativo

```bash
# Ver información del sistema
cat /etc/os-release

# Ver versión del kernel
uname -r

# Ver recursos disponibles
free -h
df -h
nproc
```

**Requisitos mínimos:**
- RAM: 4GB mínimo (8GB recomendado)
- CPU: 2 cores mínimo (4 cores recomendado)
- Almacenamiento: 50GB mínimo (SSD recomendado)
- SO: Ubuntu 20.04+ / Debian 11+ / CentOS 8+

---

## 🔄 Paso 3: Actualizar el Sistema

```bash
# Actualizar lista de paquetes
apt update

# Actualizar sistema (Ubuntu/Debian)
apt upgrade -y

# O si es CentOS/RHEL:
# yum update -y
```

---

## 🐳 Paso 4: Instalar Docker

```bash
# Instalar Docker usando el script oficial
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Verificar instalación
docker --version
```

---

## 📦 Paso 5: Instalar Docker Compose

```bash
# Instalar Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# Dar permisos de ejecución
chmod +x /usr/local/bin/docker-compose

# Verificar instalación
docker-compose --version
```

---

## 🔥 Paso 6: Configurar Firewall (UFW)

```bash
# Verificar si UFW está instalado
which ufw

# Si no está instalado, instalarlo
apt install ufw -y

# Verificar estado actual
ufw status

# Permitir SSH (IMPORTANTE: hacerlo primero para no perder acceso)
ufw allow ssh
ufw allow 22/tcp

# Permitir HTTP y HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# Habilitar firewall
ufw enable

# Verificar estado
ufw status
```

---

## 🔒 Paso 7: Configurar Seguridad SSH (Opcional pero Recomendado)

```bash
# Editar configuración SSH
nano /etc/ssh/sshd_config

# Cambios recomendados:
# - PermitRootLogin yes (o no, según preferencia)
# - PasswordAuthentication yes (o no, si usas claves)
# - Port 22 (o cambiar a otro puerto)

# Reiniciar servicio SSH
systemctl restart sshd

# Verificar que SSH sigue funcionando antes de cerrar la sesión
```

---

## 👤 Paso 8: Crear Usuario No-Root (Opcional pero Recomendado)

```bash
# Crear nuevo usuario
adduser deploy

# Añadir usuario al grupo docker
usermod -aG docker deploy

# Añadir usuario al grupo sudo (si es necesario)
usermod -aG sudo deploy

# Verificar grupos
groups deploy
```

---

## 📁 Paso 9: Preparar Directorios

```bash
# Crear directorio para el proyecto
mkdir -p /opt/thot-security

# Dar permisos (si creaste usuario deploy)
# chown -R deploy:deploy /opt/thot-security

# Verificar permisos
ls -la /opt/
```

---

## 🔍 Paso 10: Verificar Configuración

```bash
# Verificar Docker
docker ps

# Verificar Docker Compose
docker-compose --version

# Verificar firewall
ufw status

# Verificar espacio en disco
df -h

# Verificar memoria
free -h

# Verificar CPU
nproc
```

---

## ✅ Checklist de Configuración Inicial

- [ ] Sistema operativo identificado
- [ ] Sistema actualizado
- [ ] Docker instalado y funcionando
- [ ] Docker Compose instalado y funcionando
- [ ] Firewall configurado (puertos 22, 80, 443 abiertos)
- [ ] SSH configurado correctamente
- [ ] Directorio `/opt/thot-security` creado
- [ ] Recursos del sistema verificados (RAM, CPU, disco)

---

## 🚀 Siguiente Paso

Una vez completada la configuración inicial, puedes proceder con el despliegue:

1. Clonar el repositorio
2. Configurar variables de entorno
3. Desplegar las aplicaciones

Ver: `GUIA-DESPLIEGUE-PRODUCCION-VPS.md`

---

## 🔧 Comandos Útiles de Verificación

```bash
# Ver todos los contenedores Docker
docker ps -a

# Ver imágenes Docker
docker images

# Ver volúmenes Docker
docker volume ls

# Ver redes Docker
docker network ls

# Ver uso de recursos del sistema
htop  # (instalar con: apt install htop)

# Ver logs del sistema
journalctl -xe

# Ver espacio en disco detallado
du -sh /opt/*
```

---

## ⚠️ Notas Importantes

1. **Firewall:** Asegúrate de permitir SSH antes de habilitar el firewall
2. **Docker:** Verifica que Docker esté funcionando con `docker ps`
3. **Permisos:** Si creas un usuario no-root, asegúrate de añadirlo al grupo docker
4. **Espacio:** Verifica que haya suficiente espacio en disco antes de desplegar

---

**Última actualización:** 2025-01-27

