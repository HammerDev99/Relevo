#!/bin/bash
set -e

# Entrypoint para Relevo — Sistema de gestión de ausencias
# Basado en el patrón de gosu para manejo seguro de volúmenes y usuario no-root.

# Crear directorios de datos si no existen
mkdir -p data/database logs

# Fix ownership en directorios que pueden ser volúmenes montados por root
chown -R relevo:relevo data logs

# Asegurar que el código fuente sea descubrible por Python
# /app está en el path por defecto, pero /app/src permite importar 'relevo' y 'app' directamente
export PYTHONPATH=$PYTHONPATH:/app:/app/src

# Inicializar/Migrar base de datos si es necesario (Seed para MVP)
echo "==> Inicializando base de datos..."
gosu relevo python -m src.app.seed

# Iniciar la aplicación
echo "==> Iniciando Relevo API (uvicorn :8000)..."
exec gosu relevo uvicorn src.app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --log-level info \
    --access-log
