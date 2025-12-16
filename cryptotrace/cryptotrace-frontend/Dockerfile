# Usar una imagen base de Node.js
FROM node:18-alpine

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar los archivos de configuración
COPY package*.json ./

# Instalar dependencias
RUN npm install

# Copiar el resto del código
COPY . .

# Variables de entorno para el build (Next.js las incluirá en el bundle)
ARG NEXT_PUBLIC_API_URL=https://seguridad.idiaicox.com/api
ARG NEXT_PUBLIC_PROCESSING_URL=https://seguridad.idiaicox.com/processing
ARG NEXT_PUBLIC_OCR_URL=https://seguridad.idiaicox.com/ocr
ARG NEXT_PUBLIC_HPS_SYSTEM_URL=https://seguridad.idiaicox.com/hps

ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
ENV NEXT_PUBLIC_PROCESSING_URL=${NEXT_PUBLIC_PROCESSING_URL}
ENV NEXT_PUBLIC_OCR_URL=${NEXT_PUBLIC_OCR_URL}
ENV NEXT_PUBLIC_HPS_SYSTEM_URL=${NEXT_PUBLIC_HPS_SYSTEM_URL}

# Construir la aplicación
RUN npm run build

# Copiar archivos necesarios para standalone (solo si existe)
RUN if [ -d ".next/standalone" ]; then \
      cp -r .next/standalone/* ./ && \
      mkdir -p .next && \
      cp -r .next/static .next/static 2>/dev/null || true && \
      cp -r public ./public 2>/dev/null || true; \
    fi

# Exponer el puerto
EXPOSE 3000

# Comando para ejecutar: usar standalone si existe, sino usar npm start
CMD sh -c 'if [ -f "server.js" ]; then node server.js; else npm run start; fi' 