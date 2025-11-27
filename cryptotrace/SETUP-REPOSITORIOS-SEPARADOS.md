# 📁 Configuración para Repositorios Separados

## 🎯 Estructura Real del Proyecto

CryptoTrace está organizado en **repositorios separados**, no como monorepo:

```
cryptotrace/ (directorio principal en VPS)
├── cryptotrace-backend/        # Repositorio separado
├── cryptotrace-frontend/       # Repositorio separado  
├── cryptotrace-ocr/           # Repositorio separado
├── cryptotrace-pdf-generator/ # Repositorio separado
├── cryptotrace-processing/    # Repositorio separado
├── docker-compose.prod.yml    # Archivo de configuración
├── nginx/                     # Configuración Nginx
└── scripts/                   # Scripts de despliegue
```

## 🚀 Opciones para Despliegue

### Opción 1: Crear repositorio de configuración (RECOMENDADO)

Crear un repositorio separado solo para la configuración de producción:

```bash
# En tu local
mkdir cryptotrace-deploy
cd cryptotrace-deploy

# Copiar archivos de configuración
cp ../cryptotrace/docker-compose.prod.yml .
cp -r ../cryptotrace/nginx .
cp -r ../cryptotrace/scripts .
cp ../cryptotrace/INSTRUCCIONES-DESPLIEGUE-IDIAICOX.md .

# Inicializar repositorio
git init
git add .
git commit -m "Configuración de producción para cryptotrace.idiaicox.com"

# Subir a GitHub
git remote add origin https://github.com/tu-usuario/cryptotrace-deploy.git
git push -u origin main
```

**En el VPS:**
```bash
cd /opt
git clone git@github.com:calonsoaicox/cryptotrace-deploy.git cryptotrace
cd cryptotrace

# Clonar servicios usando SSH (sin credenciales)
git clone git@github.com:calonsoaicox/cryptotrace-backend.git
git clone git@github.com:calonsoaicox/cryptotrace-frontend.git
git clone git@github.com:calonsoaicox/cryptotrace-ocr.git
git clone git@github.com:calonsoaicox/cryptotrace-pdf-generator.git
git clone git@github.com:calonsoaicox/cryptotrace-processing.git
```

### Opción 2: Subir archivos manualmente

```bash
# En el VPS
cd /opt
sudo mkdir cryptotrace
sudo chown -R $USER:$USER cryptotrace
cd cryptotrace

# Clonar repositorios usando SSH (configurar primero las claves SSH)
git clone git@github.com:calonsoaicox/cryptotrace-backend.git
git clone git@github.com:calonsoaicox/cryptotrace-frontend.git
git clone git@github.com:calonsoaicox/cryptotrace-ocr.git
git clone git@github.com:calonsoaicox/cryptotrace-pdf-generator.git
git clone git@github.com:calonsoaicox/cryptotrace-processing.git

# Crear archivos de configuración (copiar desde local)
nano docker-compose.prod.yml
mkdir -p nginx/conf.d
nano nginx/nginx.conf
nano nginx/conf.d/cryptotrace.conf
mkdir scripts
nano scripts/deploy.sh
nano scripts/build-frontend.sh
nano scripts/setup-letsencrypt.sh
chmod +x scripts/*.sh
```

### Opción 3: Usar SCP/SFTP

```bash
# Desde tu local, subir archivos de configuración
scp docker-compose.prod.yml user@tu-vps:/opt/cryptotrace/
scp -r nginx/ user@tu-vps:/opt/cryptotrace/
scp -r scripts/ user@tu-vps:/opt/cryptotrace/
```

## 🔧 Actualizar docker-compose.prod.yml para repositorios separados

El archivo actual ya está correcto, pero verificar las rutas:

```yaml
services:
  backend:
    build:
      context: ./cryptotrace-backend     # ✅ Correcto
      dockerfile: docker/Dockerfile
  
  processing:
    build:
      context: ./cryptotrace-processing # ✅ Correcto
      dockerfile: Dockerfile
  
  ocr:
    build:
      context: ./cryptotrace-ocr        # ✅ Correcto
      dockerfile: Dockerfile
  
  pdf-generator:
    build:
      context: ./cryptotrace-pdf-generator # ✅ Correcto
      dockerfile: Dockerfile
```

## 📄 Archivos de configuración necesarios

Estos archivos deben estar en el directorio raíz `/opt/cryptotrace/`:

1. **docker-compose.prod.yml** - Configuración de servicios
2. **nginx/nginx.conf** - Configuración principal de Nginx
3. **nginx/conf.d/cryptotrace.conf** - Virtual host para tu dominio
4. **scripts/deploy.sh** - Script de despliegue
5. **scripts/build-frontend.sh** - Build del frontend
6. **scripts/setup-letsencrypt.sh** - Configuración SSL
7. **cryptotrace-backend/.env.prod** - Variables de entorno (crear desde ejemplo)

## 🎯 Comandos de actualización

### Actualizar un servicio específico
```bash
cd /opt/cryptotrace/cryptotrace-backend
git pull origin main
cd ..
docker-compose -f docker-compose.prod.yml up -d --build backend
```

### Actualizar todos los servicios
```bash
cd /opt/cryptotrace

# Opción 1: Script automatizado (sin credenciales)
./scripts/update-repos.sh

# Opción 2: Manual
cd cryptotrace-backend && git pull origin main && cd ..
cd cryptotrace-frontend && git pull origin main && cd ..
cd cryptotrace-ocr && git pull origin main && cd ..
cd cryptotrace-pdf-generator && git pull origin main && cd ..
cd cryptotrace-processing && git pull origin main && cd ..
./scripts/deploy.sh
```

## 📋 Checklist de Despliegue

- [ ] Todos los repositorios clonados en `/opt/cryptotrace/`
- [ ] Archivos de configuración copiados al directorio raíz
- [ ] Variables de entorno configuradas (`.env.prod`)
- [ ] Permisos de ejecución dados a scripts
- [ ] Node.js instalado en el VPS (para build del frontend)
- [ ] Docker y Docker Compose instalados

**¿Qué opción prefieres para manejar los archivos de configuración?** 