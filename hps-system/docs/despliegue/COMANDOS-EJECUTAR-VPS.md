# 🚀 Comandos para Ejecutar en la VPS - Paso a Paso

## 📋 Información de tu VPS

- **IP**: 46.183.119.90
- **Dominio**: hps.aicoxidi.com
- **Usuario**: root
- **Contraseña**: XJrdNfXBm2k-7HG

---

## 🔐 PASO 1: Conectar a la VPS

Abre tu terminal (PowerShell en Windows, Terminal en Mac/Linux) y ejecuta:

```bash
ssh root@46.183.119.90
```

Cuando te pida la contraseña, escribe: `XJrdNfXBm2k-7HG`

✅ **Verificar**: ¿Te conectaste exitosamente? Deberías ver algo como:
```
Welcome to Ubuntu...
root@tu-servidor:~#
```

---

## 📥 PASO 2: Descargar y Ejecutar el Script de Despliegue

Una vez conectado, ejecuta estos comandos **uno por uno**:

```bash
# Crear directorio temporal
mkdir -p /tmp/hps-deploy
cd /tmp/hps-deploy

# Descargar el script de despliegue
curl -o despliegue.sh https://raw.githubusercontent.com/calonsoaicox/hps-system/desarrollo-pajuelo/docs/despliegue/script-despliegue-completo.sh

# Hacer ejecutable
chmod +x despliegue.sh

# Ejecutar el script
./despliegue.sh
```

**O si prefieres copiar y pegar el script directamente:**

```bash
# Crear el script directamente
cat > /tmp/despliegue.sh << 'SCRIPT_END'
```

Luego copia todo el contenido del archivo `script-despliegue-completo.sh` y pégalo, seguido de:

```bash
SCRIPT_END

chmod +x /tmp/despliegue.sh
/tmp/despliegue.sh
```

---

## ⚙️ PASO 3: Configurar Credenciales (Cuando el script lo pida)

El script te pedirá que edites el archivo `.env`. Necesitarás configurar:

1. **OPENAI_API_KEY**: Tu clave de OpenAI
2. **SMTP_PASSWORD**: Contraseña del email (seguridad@idiaicox.com)
3. **IMAP_PASSWORD**: Misma contraseña del email

Para editar:

```bash
nano /opt/hps-system/.env
```

**Busca estas líneas y reemplaza los valores:**

```bash
OPENAI_API_KEY=TU_OPENAI_API_KEY_AQUI          # ← Reemplazar
SMTP_PASSWORD=TU_PASSWORD_EMAIL_AQUI           # ← Reemplazar
IMAP_PASSWORD=TU_PASSWORD_EMAIL_AQUI           # ← Reemplazar
```

**Para guardar en nano**: Presiona `Ctrl+X`, luego `Y`, luego `Enter`

---

## 🌐 PASO 4: Configurar DNS (IMPORTANTE)

Antes de obtener el certificado SSL, asegúrate de que el DNS está configurado:

1. Ve al panel de tu proveedor DNS (donde está registrado `aicoxidi.com`)
2. Crea un registro **A**:
   - **Nombre**: `hps` (o `@` para dominio raíz)
   - **Tipo**: A
   - **Valor**: `46.183.119.90`
   - **TTL**: 3600

3. Espera unos minutos para que se propague

4. Verifica que funciona:
   ```bash
   # Desde tu máquina local (NO en la VPS)
   nslookup hps.aicoxidi.com
   # Debería mostrar: 46.183.119.90
   ```

---

## ✅ PASO 5: Verificar el Despliegue

Una vez que el script termine, verifica:

```bash
# Ver estado de servicios
cd /opt/hps-system
docker compose ps

# Todos deberían estar "Up" y "healthy"
```

**Deberías ver algo como:**
```
NAME                  STATUS          PORTS
hps_backend           Up (healthy)    ...
hps_frontend          Up (healthy)    ...
hps_postgres          Up (healthy)    ...
hps_agente_ia         Up (healthy)    ...
hps_redis             Up (healthy)    ...
hps_celery_worker     Up (healthy)    ...
```

---

## 🔍 PASO 6: Ver Logs (Si hay problemas)

```bash
# Ver todos los logs
cd /opt/hps-system
docker compose logs -f

# Ver logs de un servicio específico
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f db
```

---

## 🌐 PASO 7: Acceder a la Aplicación

Abre tu navegador y ve a:

**https://hps.aicoxidi.com**

Deberías ver la página de login del Sistema HPS.

---

## 🆘 Si Algo Sale Mal

### Problema: "No se puede conectar por SSH"

**Solución**: Verifica que el puerto 22 esté abierto en el firewall de Clouding.

### Problema: "Docker no se instala"

**Solución**: Ejecuta manualmente:
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
```

### Problema: "Error al obtener certificado SSL"

**Solución**: Verifica que el DNS esté configurado correctamente:
```bash
# En la VPS
curl -I http://hps.aicoxidi.com
```

### Problema: "Los servicios no inician"

**Solución**: Verifica los logs:
```bash
cd /opt/hps-system
docker compose logs
```

### Problema: "No puedo acceder al sitio"

**Solución**: 
1. Verifica que Nginx esté corriendo: `systemctl status nginx`
2. Verifica que los contenedores estén corriendo: `docker compose ps`
3. Verifica los logs de Nginx: `tail -f /var/log/nginx/error.log`

---

## 📝 Comandos Útiles de Mantenimiento

```bash
# Reiniciar todos los servicios
cd /opt/hps-system
docker compose restart

# Reiniciar un servicio específico
docker compose restart backend

# Actualizar la aplicación (después de git pull)
docker compose build
docker compose up -d

# Ver uso de recursos
docker stats

# Ver espacio en disco
df -h

# Verificar firewall
ufw status
```

---

## ✅ Checklist Final

- [ ] ¿Te conectaste a la VPS?
- [ ] ¿Se ejecutó el script sin errores?
- [ ] ¿Configuraste el archivo .env con tus credenciales?
- [ ] ¿Configuraste el DNS?
- [ ] ¿Todos los servicios están "Up"?
- [ ] ¿Puedes acceder a https://hps.aicoxidi.com?
- [ ] ¿El SSL funciona (candado verde)?

---

**¡Listo!** 🎉 Si todo está marcado, tu aplicación está desplegada y funcionando.

