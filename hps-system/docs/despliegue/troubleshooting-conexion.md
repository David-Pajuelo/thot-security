# 🔧 Solución de Problemas de Conexión SSH

## Problema: Permission Denied

### Posibles causas y soluciones:

### 1. Verificar credenciales
- Usuario: `root` o `administrador`
- Contraseña: `XJrdNfXBm2k-7HG` (exactamente como está, sin espacios)

### 2. Intentar con usuario "administrador"
```bash
ssh administrador@46.183.119.90
```

### 3. Verificar si el servidor requiere clave SSH
El servidor podría estar configurado solo para aceptar claves SSH, no contraseñas.

### 4. Contactar con el proveedor (Clouding.host)
Si nada funciona, puede que:
- El usuario root esté deshabilitado
- Se requiera una clave SSH
- La contraseña haya cambiado

### 5. Usar el panel de Clouding.host
Muchos proveedores VPS tienen:
- Consola web (VNC) para acceder directamente
- Panel de control para resetear contraseña
- Gestión de claves SSH

### 6. Verificar información de acceso
Revisa el email de bienvenida de Clouding.host, podría tener:
- Credenciales diferentes
- Instrucciones de acceso
- Panel de control con acceso web

