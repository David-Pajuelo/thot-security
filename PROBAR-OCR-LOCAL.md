# Instrucciones para Probar OCR en Desarrollo Local

## 1. Verificar que el servicio OCR esté corriendo

```bash
cd cryptotrace
docker compose ps ocr
```

## 2. Reconstruir el servicio OCR con los nuevos cambios

```bash
cd cryptotrace
docker compose build ocr
docker compose up -d ocr
```

## 3. Verificar que el .env del OCR tenga la API key de OpenAI

```bash
# Verificar que existe el archivo .env
cat cryptotrace-ocr/.env | grep OPENAI_API_KEY

# Si no existe, crearlo desde el .env del backend
# (Asegúrate de que la API key esté en una sola línea)
```

## 4. Ver logs del OCR en tiempo real

```bash
docker compose logs -f ocr
```

## 5. Probar el endpoint del OCR directamente

```bash
# Verificar que el servicio responde
curl http://localhost:8002/

# Debería devolver: {"message":"CryptoTrace OCR Service","status":"running"}
```

## 6. Probar desde el frontend

1. Asegúrate de que el frontend esté corriendo:
```bash
docker compose ps frontend
```

2. Si no está corriendo:
```bash
docker compose up -d frontend
```

3. Accede a: http://localhost:3000

4. Ve a la sección de subir AC21 y prueba subir una imagen o PDF

5. Observa los logs del OCR en tiempo real:
```bash
docker compose logs -f ocr
```

## 7. Verificar los logs detallados

Con los nuevos cambios, deberías ver en los logs del OCR:
- `🖼️ Iniciando procesamiento de imagen...`
- `✅ Imagen codificada en base64`
- `📞 Llamando a OpenAI API...`
- `✅ Respuesta recibida de OpenAI`
- `================== RAW OPENAI RESPONSE ==================`
- `================== PARSED JSON DATA =====================`
- `================== FINAL PROCESSED DATA =================`
- `📊 Resumen: X artículos, Y accesorios`

Si ves errores, los logs mostrarán:
- `❌ Error al parsear JSON de OpenAI`
- `❌ Error en el procesamiento`

## 8. Si hay problemas con la API key

```bash
# Verificar que la API key esté en el contenedor
docker compose exec ocr python -c "import os; print('API Key presente:', bool(os.getenv('OPENAI_API_KEY')))"
```

