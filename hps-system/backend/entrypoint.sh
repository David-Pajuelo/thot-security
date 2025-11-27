#!/bin/bash
set -e

echo "🚀 Iniciando contenedor HPS Backend..."

# Función para esperar a que la base de datos esté disponible
wait_for_db() {
    echo "🔄 Esperando a que la base de datos esté disponible..."
    
    # Obtener variables de entorno
    DB_HOST=${POSTGRES_HOST:-db}
    DB_PORT=${POSTGRES_PORT:-5432}
    DB_USER=${POSTGRES_USER:-hps_user}
    DB_PASS=${POSTGRES_PASSWORD:-hps_password_secure}
    DB_NAME=${POSTGRES_DB:-hps_system}
    
    # Esperar hasta que PostgreSQL esté listo
    until PGPASSWORD=$DB_PASS psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c '\q' 2>/dev/null; do
        echo "⏳ Base de datos no disponible, esperando..."
        sleep 2
    done
    
    echo "✅ Base de datos disponible"
}

# Función para ejecutar migraciones
run_migrations() {
    echo "🔄 Ejecutando migraciones de base de datos..."
    
    # Cambiar al directorio de la aplicación
    cd /app
    
    # Ejecutar migraciones con Alembic
    if alembic upgrade head; then
        echo "✅ Migraciones ejecutadas correctamente"
    else
        echo "⚠️ Error ejecutando migraciones, pero continuando..."
    fi
}

# Función para verificar si las tablas existen
check_tables() {
    echo "🔍 Verificando estructura de base de datos..."
    
    DB_HOST=${POSTGRES_HOST:-db}
    DB_PORT=${POSTGRES_PORT:-5432}
    DB_USER=${POSTGRES_USER:-hps_user}
    DB_PASS=${POSTGRES_PASSWORD:-hps_password_secure}
    DB_NAME=${POSTGRES_DB:-hps_system}
    
    # Verificar si la tabla hps_requests existe
    if PGPASSWORD=$DB_PASS psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'hps_requests');" | grep -q "t"; then
        echo "✅ Tablas de base de datos verificadas"
        return 0
    else
        echo "❌ Tablas de base de datos no encontradas"
        return 1
    fi
}

# Función principal
main() {
    # Esperar a que la base de datos esté disponible
    wait_for_db
    
    # Verificar si las tablas existen
    if ! check_tables; then
        echo "🔄 Ejecutando migraciones para crear tablas..."
        run_migrations
    else
        echo "✅ Base de datos ya está configurada"
    fi
    
    # Verificar estructura final
    if check_tables; then
        echo "🎉 Base de datos lista para usar"
    else
        echo "❌ Error: Las tablas no se crearon correctamente"
        exit 1
    fi
    
    # Poblar datos iniciales si es necesario
    echo "🌱 Verificando datos iniciales..."
    if python -c "from src.database.seed_data import main; main()"; then
        echo "✅ Datos iniciales verificados"
    else
        echo "⚠️ Error poblando datos iniciales, pero continuando..."
    fi
    
    # Iniciar la aplicación
    echo "🚀 Iniciando aplicación FastAPI..."
    exec python -m uvicorn src.main:app --host 0.0.0.0 --port 8001 --reload
}

# Ejecutar función principal
main "$@"
