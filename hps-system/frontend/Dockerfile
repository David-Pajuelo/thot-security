FROM node:18-alpine

WORKDIR /app

# Instalar dependencias del sistema
RUN apk add --no-cache curl

# Recibir argumentos de build (variables de entorno de React)
ARG REACT_APP_API_URL
ARG REACT_APP_WS_URL
ARG REACT_APP_AGENTE_IA_WS_URL

# Convertir ARG a ENV para que estén disponibles durante el build
ENV REACT_APP_API_URL=$REACT_APP_API_URL
ENV REACT_APP_WS_URL=$REACT_APP_WS_URL
ENV REACT_APP_AGENTE_IA_WS_URL=$REACT_APP_AGENTE_IA_WS_URL

# Copiar package.json y package-lock.json
COPY package*.json ./

# Instalar dependencias (incluyendo devDependencies para Tailwind CSS)
RUN npm install

# Copiar código fuente
COPY . .

# Exponer puerto
EXPOSE 3000

# Comando de inicio
CMD ["npm", "start"]
