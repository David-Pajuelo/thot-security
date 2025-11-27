# Usa una imagen base con Python 3.9
FROM python:3.9

# Establece el directorio de trabajo
WORKDIR /app

# Copia los archivos del proyecto
COPY . .

# Instala las dependencias desde el archivo requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Exponer el puerto donde correrá la API
EXPOSE 5001

# Comando de inicio de la aplicación
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5001"]
