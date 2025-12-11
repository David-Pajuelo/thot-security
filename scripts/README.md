# 📜 Scripts de Despliegue

Scripts automatizados para desplegar el sistema en producción.

## 📋 Scripts Disponibles

### 1. `desplegar-produccion-completo.sh`
Script maestro que automatiza todo el proceso de despliegue desde tu máquina local.

**Uso:**
```bash
# Desplegar solo HPS System
./scripts/desplegar-produccion-completo.sh hps

# Desplegar solo CryptoTrace
./scripts/desplegar-produccion-completo.sh cryptotrace

# Desplegar ambos
./scripts/desplegar-produccion-completo.sh ambos
```

**Requisitos:**
- `sshpass` instalado: `sudo apt install sshpass` (Linux) o `brew install sshpass` (Mac)
- Acceso SSH al VPS
- Credenciales configuradas en el script

**Nota:** Este script se ejecuta desde tu máquina local y se conecta al VPS remotamente.

---

### 2. `desplegar-hps-system.sh`
Script para desplegar HPS System directamente en el VPS.

**Uso:**
```bash
# En el VPS
cd /opt/thot-security/hps-system
./desplegar-hps-system.sh
```

**Requisitos:**
- Ejecutar desde `/opt/thot-security/hps-system`
- Archivo `.env.prod` configurado
- Docker y Docker Compose instalados

---

### 3. `desplegar-cryptotrace.sh`
Script para desplegar CryptoTrace directamente en el VPS.

**Uso:**
```bash
# En el VPS
cd /opt/thot-security/cryptotrace
./desplegar-cryptotrace.sh
```

**Requisitos:**
- Ejecutar desde `/opt/thot-security/cryptotrace`
- Archivo `cryptotrace-backend/.env.prod` configurado
- Docker y Docker Compose instalados

---

## 🚀 Flujo de Despliegue Recomendado

### Opción 1: Despliegue Automatizado (Desde Local)

1. **Preparar scripts:**
   ```bash
   chmod +x scripts/*.sh
   ```

2. **Instalar sshpass (si no está instalado):**
   ```bash
   # Linux
   sudo apt install sshpass
   
   # Mac
   brew install sshpass
   ```

3. **Ejecutar despliegue:**
   ```bash
   ./scripts/desplegar-produccion-completo.sh hps
   ```

4. **Configurar variables de entorno en el VPS:**
   ```bash
   ssh root@46.183.119.90
   cd /opt/thot-security/hps-system
   nano .env.prod  # Editar con las credenciales
   ```

5. **Re-ejecutar despliegue si es necesario:**
   ```bash
   cd /opt/thot-security/hps-system
   ./desplegar-hps-system.sh
   ```

### Opción 2: Despliegue Manual (En el VPS)

1. **Conectar al VPS:**
   ```bash
   ssh root@46.183.119.90
   ```

2. **Clonar repositorio:**
   ```bash
   cd /opt
   git clone -b production https://github.com/David-Pajuelo/thot-security.git
   cd thot-security
   ```

3. **Configurar variables de entorno:**
   ```bash
   cd hps-system
   cp env.prod.example .env.prod
   nano .env.prod  # Editar con las credenciales
   ```

4. **Ejecutar script de despliegue:**
   ```bash
   chmod +x desplegar-hps-system.sh
   ./desplegar-hps-system.sh
   ```

---

## ⚙️ Configuración de Variables de Entorno

Antes de ejecutar los scripts, asegúrate de configurar las variables de entorno:

### HPS System
- Archivo: `/opt/thot-security/hps-system/.env.prod`
- Ver: `CONFIGURACION-PRODUCCION-RESUMEN.md`

### CryptoTrace
- Archivo: `/opt/thot-security/cryptotrace/cryptotrace-backend/.env.prod`
- Ver: `CONFIGURACION-PRODUCCION-RESUMEN.md`

---

## 🔧 Solución de Problemas

### Error: "No se encontró docker-compose.prod.yml"
- Verifica que estás en el directorio correcto
- Verifica que el repositorio está clonado correctamente

### Error: "No se encontró .env.prod"
- Copia el archivo de ejemplo: `cp env.prod.example .env.prod`
- Edita el archivo con las credenciales correctas

### Error: "Contenedores no responden"
- Revisa los logs: `docker-compose -f docker-compose.prod.yml logs -f`
- Verifica que las variables de entorno están correctas
- Verifica que los puertos no están en uso

### Error de conexión SSH
- Verifica que el VPS está accesible: `ping 46.183.119.90`
- Verifica las credenciales SSH
- Verifica que el firewall permite conexiones SSH

---

## 📝 Notas

- Los scripts están diseñados para ser idempotentes (se pueden ejecutar múltiples veces)
- Los scripts detienen contenedores existentes antes de levantar nuevos
- Los scripts verifican la salud de los servicios después del despliegue
- Se recomienda revisar los logs después del despliegue

---

**Última actualización:** 2025-01-27

