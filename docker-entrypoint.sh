#!/bin/bash
set -e

# Entrypoint para Relevo — Sistema de gestión de ausencias
# Basado en el patrón de gosu para manejo seguro de volúmenes y usuario no-root.

# Crear directorios de datos si no existen
mkdir -p data/database logs

# Fix ownership en directorios que pueden ser volúmenes montados por root
# UID 1000 corresponde al usuario 'relevo' creado en el Dockerfile
chown -R relevo:relevo data logs

# Inicializar/Migrar base de datos si es necesario (Seed para MVP)
# En una app real usaríamos Alembic, aquí usamos el script de seed para asegurar admin inicial
echo "==> Inicializando base de datos..."
gosu relevo python -m src.app.seed

# Iniciar la aplicación
echo "==> Iniciando Relevo API (uvicorn :8000)..."
exec gosu relevo uvicorn src.app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --log-level info \
    --access-log
