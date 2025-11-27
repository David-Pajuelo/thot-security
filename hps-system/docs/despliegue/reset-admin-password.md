# Resetear Contraseña de Administrador

## Verificar usuarios existentes

```bash
docker compose exec db psql -U hps_user -d hps_system -c "SELECT id, email, role_name, is_active FROM users WHERE role_name = 'admin' OR role_name = 'administrator';"
```

## Ver todos los usuarios

```bash
docker compose exec db psql -U hps_user -d hps_system -c "SELECT id, email, first_name, last_name, role_name, is_active FROM users;"
```

## Resetear contraseña de administrador

### Opción 1: Usando Python (genera hash bcrypt)

```bash
docker compose exec backend python3 << 'EOF'
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
new_password = "Admin123!"  # Cambia esta contraseña
hashed = pwd_context.hash(new_password)
print(f"Password hash: {hashed}")
EOF
```

Luego actualiza en la BD:

```bash
docker compose exec db psql -U hps_user -d hps_system -c "UPDATE users SET password_hash = 'HASH_AQUI' WHERE email = 'tu-email-admin@example.com';"
```

### Opción 2: Crear nuevo usuario administrador

```bash
docker compose exec backend python3 << 'EOF'
from passlib.context import CryptContext
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
password = "Admin123!"  # Cambia esta contraseña
hashed = pwd_context.hash(password)

print(f"Password hash: {hashed}")
print(f"Usa este hash para crear el usuario en la BD")
EOF
```

