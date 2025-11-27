# Usar una imagen oficial de Python.
# python:3.9-slim o python:3.10-slim son buenas opciones para reducir el tamaño.
FROM python:3.9-slim

# Establecer el directorio de trabajo en el contenedor
WORKDIR /usr/src/app

# Instalar dependencias de sistema para WeasyPrint y otras necesidades.
# Estas son comunes para Debian/Ubuntu. Pueden necesitar ajustes.
# libffi-dev y pkg-config son a menudo necesarias para construir algunas dependencias de Python.
# fontconfig es para el manejo de fuentes por WeasyPrint.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libcairo2 \
    libgdk-pixbuf-xlib-2.0-0 \
    libffi-dev \
    pkg-config \
    fontconfig \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copiar el archivo de dependencias primero para aprovechar el cache de Docker
COPY requirements.txt ./

# Instalar las dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código de la aplicación al directorio de trabajo
COPY ./app /usr/src/app/app

# Exponer el puerto en el que corre la aplicación Flask/Gunicorn
EXPOSE 5003

# Comando para correr la aplicación usando Gunicorn.
# Asegúrate de que 'main:app' coincida con el nombre de tu archivo .py (main.py) y la instancia de Flask (app).
# El directorio de trabajo ya es /usr/src/app, y main.py está en app/main.py
# Gunicorn necesita estar en requirements.txt
CMD ["gunicorn", "--workers", "2", "--bind", "0.0.0.0:5003", "app.main:app"] 