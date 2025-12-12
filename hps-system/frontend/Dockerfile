FROM node:18-alpine AS builder

WORKDIR /app

# Instalar dependencias del sistema
RUN apk add --no-cache curl

# Recibir argumentos de build (variables de entorno de React)
ARG REACT_APP_API_URL
ARG REACT_APP_WS_URL
ARG REACT_APP_AGENTE_IA_WS_URL
ARG REACT_APP_CRYPTOTRACE_URL

# Convertir ARG a ENV para que estén disponibles durante el build
ENV REACT_APP_API_URL=$REACT_APP_API_URL
ENV REACT_APP_WS_URL=$REACT_APP_WS_URL
ENV REACT_APP_AGENTE_IA_WS_URL=$REACT_APP_AGENTE_IA_WS_URL
ENV REACT_APP_CRYPTOTRACE_URL=$REACT_APP_CRYPTOTRACE_URL
ENV NODE_ENV=production

# Copiar package.json y package-lock.json
COPY package*.json ./

# Instalar dependencias
RUN npm install

# Copiar código fuente
COPY . .

# Construir la aplicación
RUN npm run build

# Etapa de producción con nginx
FROM nginx:alpine

# Copiar archivos construidos desde la etapa builder
COPY --from=builder /app/build /usr/share/nginx/html

# Copiar configuración de nginx personalizada para SPA
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Exponer puerto
EXPOSE 80

# Comando de inicio
CMD ["nginx", "-g", "daemon off;"]
