# Comandos para actualizar OCR en VPS

## Pasos para aplicar los cambios del OCR

```bash
# 1. Ir al directorio del proyecto
cd /opt/thot-security

# 2. Hacer pull de la rama production
git pull origin production

# 3. Ir al directorio de CryptoTrace
cd cryptotrace

# 4. Reconstruir el servicio OCR (IMPORTANTE: con --no-cache para forzar rebuild)
docker compose -f docker-compose.prod.yml build --no-cache ocr

# 5. Reiniciar el contenedor del OCR
docker compose -f docker-compose.prod.yml up -d ocr

# 6. Verificar que el contenedor está corriendo
docker compose -f docker-compose.prod.yml ps ocr

# 7. Ver logs para verificar que todo está bien
docker compose -f docker-compose.prod.yml logs -f ocr
```

## Comandos en una sola línea (opcional)

```bash
cd /opt/thot-security && git pull origin production && cd cryptotrace && docker compose -f docker-compose.prod.yml build --no-cache ocr && docker compose -f docker-compose.prod.yml up -d ocr
```

## Verificar que la API key está actualizada

**IMPORTANTE**: Asegúrate de que el archivo `cryptotrace-ocr/.env.prod` en la VPS tenga la nueva API key de OpenAI actualizada.

```bash
# Verificar que la API key está presente
cat cryptotrace-ocr/.env.prod | grep OPENAI_API_KEY
```

## Probar el OCR

Después de reconstruir, prueba subir una imagen o PDF desde el frontend. Con los logs mejorados, deberías ver:
- `🖼️ Iniciando procesamiento de imagen...`
- `✅ Imagen codificada en base64`
- `📞 Llamando a OpenAI API...`
- `✅ Respuesta recibida de OpenAI`
- `================== RAW OPENAI RESPONSE ==================`
- `================== PARSED JSON DATA =====================`
- `================== FINAL PROCESSED DATA =================`
- `📊 Resumen: X artículos, Y accesorios`

