#!/bin/bash
set -e

# Entrypoint para Relevo — Sistema de gestión de ausencias
# Basado en el patrón de gosu para manejo seguro de volúmenes y usuario no-root.

# Crear directorios de datos si no existen
mkdir -p data/database logs

# Fix ownership en directorios que pueden ser volúmenes montados por root
chown -R relevo:relevo data logs

# Asegurar que el código fuente sea descubrible por Python
export PYTHONPATH=$PYTHONPATH:/app:/app/src

# --- Selección de Modo (RELEVO_MODE) ---

case "${RELEVO_MODE:-api}" in
  api)
    # Inicializar/Migrar base de datos si es necesario (Solo en modo API para evitar race conditions)
    echo "==> Inicializando base de datos (Modo API)..."
    gosu relevo python -m src.app.seed

    echo "==> Iniciando Relevo API (uvicorn :8000)..."
    exec gosu relevo uvicorn src.app.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --log-level info \
        --access-log
    ;;
    
  gui)
    echo "==> Iniciando Relevo GUI (Streamlit :8501)..."
    exec gosu relevo streamlit run src/app/gui/app.py \
        --server.port=8501 \
        --server.address=0.0.0.0 \
        --server.headless=true \
        --browser.gatherUsageStats=false
    ;;

  *)
    echo "ERROR: RELEVO_MODE debe ser 'api' o 'gui'"
    exit 1
    ;;
esac
