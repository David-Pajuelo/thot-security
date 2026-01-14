# Mapeo de Puertos - thot-security

## cryptotrace
- **Backend Django**: `8080:8080`
- **Frontend Next.js**: `3000:3000`
- **Processing**: `5001:5001`
- **OCR**: `8002:8000`
- **PDF Generator**: `5003:5003`
- **PostgreSQL**: `5432:5432`
- **Redis**: `6379:6379`

## hps-system
- **Frontend React**: `3001:3000` ✅ (sin conflicto)
- **Agente IA**: `8000:8000` ✅ (sin conflicto)
- **Redis**: `6379:6379` ❌ (CONFLICTO con cryptotrace-redis)

## Solución
- **hps-system** usará el Redis compartido de cryptotrace (no necesita su propio Redis)
- Ambos sistemas comparten la misma base de datos PostgreSQL (cryptotrace-db)

