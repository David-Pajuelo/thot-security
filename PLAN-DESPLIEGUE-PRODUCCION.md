# 📋 Plan de Despliegue en Producción

## 🎯 Objetivo

Desplegar el sistema completo (HPS System + CryptoTrace) en el VPS de producción usando el dominio `seguridad.idiaicox.com`.

## 📌 Información del VPS

- **IP:** `187.33.154.156`
- **Usuario:** `root`
- **Contraseña:** `41c0x1d1!`
- **Dominio:** `seguridad.idiaicox.com` (para ambas aplicaciones)

## 🚀 Estrategia de Despliegue

### Fase 1: Preparación (Local)
1. ✅ Crear rama `production` en Git
2. ✅ Actualizar documentación con dominio correcto
3. ✅ Generar credenciales de producción

### Fase 2: Preparación del VPS
1. ✅ Verificar que Docker está instalado
2. ✅ Configurar firewall
3. ✅ Clonar repositorio

### Fase 3: Desplegar HPS System (Prioritario)
1. Configurar variables de entorno
2. Construir y levantar contenedores
3. Ejecutar migraciones
4. Configurar Nginx
5. Obtener certificado SSL
6. Verificar funcionamiento

### Fase 4: Desplegar CryptoTrace (Cuando dominio esté listo)
1. Configurar variables de entorno
2. Construir y levantar contenedores
3. Ejecutar migraciones
4. Recolectar archivos estáticos
5. Configurar Nginx (si es necesario)
6. Verificar funcionamiento

## 📝 Checklist de Despliegue

### Pre-despliegue
- [ ] Rama `production` creada y subida a Git
- [ ] Documentación actualizada
- [ ] Credenciales generadas y documentadas

### VPS - Preparación
- [ ] Docker y Docker Compose instalados
- [ ] Firewall configurado (puertos 22, 80, 443)
- [ ] Repositorio clonado en `/opt/thot-security`
- [ ] Dominio `seguridad.idiaicox.com` apuntando a la IP del VPS

### HPS System
- [ ] Variables de entorno configuradas (`.env.prod`)
- [ ] Contenedores construidos
- [ ] Contenedores levantados y funcionando
- [ ] Migraciones ejecutadas
- [ ] Nginx configurado
- [ ] Certificado SSL obtenido
- [ ] Sistema accesible vía HTTPS
- [ ] Login funcionando

### CryptoTrace (Pendiente - dominio no listo)
- [ ] Variables de entorno configuradas (`.env.prod`)
- [ ] Contenedores construidos
- [ ] Contenedores levantados y funcionando
- [ ] Migraciones ejecutadas
- [ ] Archivos estáticos recolectados
- [ ] Nginx configurado (si es necesario)
- [ ] Sistema accesible vía HTTPS
- [ ] Login funcionando

## 🔧 Orden de Ejecución Recomendado

1. **Primero:** Desplegar HPS System (dominio listo)
2. **Después:** Desplegar CryptoTrace (cuando dominio esté configurado)

## 📞 Notas Importantes

- El dominio `seguridad.idiaicox.com` debe apuntar a `187.33.154.156` antes de obtener el certificado SSL
- Ambas aplicaciones compartirán el mismo dominio, por lo que Nginx deberá enrutar según la ruta o subdominio
- Se recomienda usar subdominios o rutas diferentes para cada aplicación:
  - HPS System: `seguridad.idiaicox.com` o `hps.seguridad.idiaicox.com`
  - CryptoTrace: `cryptotrace.seguridad.idiaicox.com` o `seguridad.idiaicox.com/cryptotrace`

---

**Última actualización:** 2025-01-27

