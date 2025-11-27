# Imagen base con Python 3.9
FROM python:3.9

# Instalar dependencias del sistema (incluye el cliente PostgreSQL)
RUN apt-get update && apt-get install -y postgresql-client

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar los archivos de requerimientos
COPY docker/requirements.txt /app/requirements.txt

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Crear directorio de logs y asegurar permisos
RUN mkdir -p /app/logs && \
    chmod -R 777 /app/logs && \
    touch /app/logs/django.log && \
    chmod 666 /app/logs/django.log

# Copiar el código fuente del backend
COPY src /app

# Exponer el puerto para el servidor Django
EXPOSE 8080

# Comando para ejecutar Django en modo desarrollo
CMD ["python", "manage.py", "runserver", "0.0.0.0:8080"]
