¡Excelente trabajo! Los cambios de compatibilidad están completos. Ahora te doy las instrucciones paso a paso para eldespliegue en el VPS.

─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

🚀 Instrucciones de Despliegue VPS - Relevo

Requisitos Previos

  • Imagen Docker disponible en GHCR: ghcr.io/hammerdev99/relevo:latest
  • Acceso a EasyPanel: https://panel.sprintjudicial.com
  • Acceso SSH al VPS

─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

Paso 1: Configuración DNS

  1. Crear registro DNS para la GUI:
    • Tipo: A
    • Nombre: relevo
    • Valor: IP del VPS (31.97.146.7)
    • TTL: 3600
  2. NO crear registro DNS para la API (será interna)

Verificar DNS:

# Desde tu máquina local
dig relevo.sprintjudicial.com
nslookup relevo.sprintjudicial.com

─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

Paso 2: Crear Directorios de Volúmenes en VPS

# SSH al VPS
ssh sprintadmin@31.97.146.7

# Crear directorios para volúmenes
sudo mkdir -p /etc/easypanel/projects/sprintjudicial/relevo-gui/volumes/database
sudo mkdir -p /etc/easypanel/projects/sprintjudicial/relevo-gui/volumes/logs

# Establecer permisos correctos (UID 1000 = usuario relevo en contenedor)
sudo chown -R 1000:1000 /etc/easypanel/projects/sprintjudicial/relevo-gui/volumes/

# Verificar
ls -la /etc/easypanel/projects/sprintjudicial/relevo-gui/volumes/

─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

Paso 3: Crear Servicio API en EasyPanel (PRIMERO)

  1. Acceder a EasyPanel: https://panel.sprintjudicial.com
  2. Crear nuevo servicio:
    • Click en "Create Service"
    • Service Name: relevo-api
    • Image: ghcr.io/hammerdev99/relevo:latest
    • Port: 8000 (interno, NO exponer)
  3. Variables de Entorno:

RELEVO_MODE=api
SECRET_KEY=<generar-clave-segura-64-chars>
DATABASE_URL=sqlite:////app/data/database/relevo.db
TZ=America/Bogota

Generar SECRET_KEY seguro:

openssl rand -hex 32

  4. Volúmenes (Mounts):

relevo-database → /app/data/database
relevo-logs → /app/logs

Configuración de Mounts en EasyPanel:

  • Type: Bind
  • Source: /etc/easypanel/projects/sprintjudicial/relevo-gui/volumes/database
  • Target: /app/data/database
  • Type: Bind
  • Source: /etc/easypanel/projects/sprintjudicial/relevo-gui/volumes/logs
  • Target: /app/logs
  5. Resources:
    • Memory Limit: 256 MB
    • Memory Reservation: 128 MB
    • CPU Limit: 0.5
  6. Domain:
    • NO configurar dominio (API será interna)
  7. Deploy y esperar a que esté healthy

─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

Paso 4: Crear Servicio GUI en EasyPanel (SEGUNDO)

  1. Crear nuevo servicio:
    • Service Name: relevo-gui
    • Image: ghcr.io/hammerdev99/relevo:latest
    • Port: 8501
  2. Variables de Entorno:

RELEVO_MODE=gui
SECRET_KEY=<misma-clave-que-api>
DATABASE_URL=sqlite:////app/data/database/relevo.db
TZ=America/Bogota

  3. Volúmenes (MISMOS que API):

relevo-database → /app/data/database
relevo-logs → /app/logs

Configuración de Mounts (IGUAL que API):

  • Type: Bind
  • Source: /etc/easypanel/projects/sprintjudicial/relevo-gui/volumes/database
  • Target: /app/data/database
  • Type: Bind
  • Source: /etc/easypanel/projects/sprintjudicial/relevo-gui/volumes/logs
  • Target: /app/logs
  4. Resources:
    • Memory Limit: 512 MB
    • Memory Reservation: 256 MB
    • CPU Limit: 0.5
  5. Domain Configuration:
    • Domain: relevo.sprintjudicial.com
    • Port: 8501
    • HTTPS: Habilitado (Let's Encrypt automático)
  6. Deploy y esperar a que esté healthy

─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

Paso 5: Verificar Despliegue

Verificar Servicios Docker

# SSH al VPS
ssh sprintadmin@31.97.146.7

# Verificar servicios
docker service ls | grep relevo

# Esperar: sprintjudicial_relevo-api   1/1
# Esperar: sprintjudicial_relevo-gui   1/1

Verificar Health Check API (Interno)

# Desde el VPS
docker ps | grep relevo-api
# Obtener container ID

docker exec <container-id-api> curl -f http://localhost:8000/
# Respuesta esperada: {"message": "Relevo API v1"}

Verificar GUI (Externo)

# Desde tu máquina local
curl -I https://relevo.sprintjudicial.com
# Esperar: HTTP/1.1 200 OK

# Probar en navegador
https://relevo.sprintjudicial.com

Verificar Comunicación GUI→API

# Ver logs de GUI buscando errores de conexión
docker service logs sprintjudicial_relevo-gui --tail 50
# Buscar: "Error de conexión con el servidor"

Verificar Base de Datos SQLite

# Verificar que el archivo existe y tiene permisos
ls -la /etc/easypanel/projects/sprintjudicial/relevo-gui/volumes/database/
# Debe haber: relevo.db con permisos 1000:1000

# Opcional: Consultar BD
sqlite3 /etc/easypanel/projects/sprintjudicial/relevo-gui/volumes/database/relevo.db "SELECT name FROM sqlite_master WHERE type='table';"

─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

Paso 6: Configurar Scripts de Monitoreo (Opcional pero Recomendado)

Crear script similar a Sherlock:

# Crear directorio de scripts Relevo
mkdir -p ~/relevo-deploy

# Crear script de health check
cat > ~/relevo-deploy/health-check-relevo.sh << 'EOF'
#!/bin/bash
SERVICE_GUI="sprintjudicial_relevo-gui"
SERVICE_API="sprintjudicial_relevo-api"
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")

# 1. Replicas GUI
REPLICAS_GUI=$(docker service ls --filter "name=${SERVICE_GUI}" --format "{{.Replicas}}" 2>/dev/null || echo "N/A")
if [[ "$REPLICAS_GUI" == "1/1" ]]; then
    echo "[${TIMESTAMP}] OK: GUI replicas ${REPLICAS_GUI}"
else
    echo "[${TIMESTAMP}] FAIL: GUI replicas ${REPLICAS_GUI}"
fi

# 2. HTTPS GUI
HTTP_GUI=$(curl -sf -o /dev/null -w "%{http_code}" \
    "https://relevo.sprintjudicial.com" 2>/dev/null || echo "000")
if [[ "$HTTP_GUI" == "200" ]]; then
    echo "[${TIMESTAMP}] OK: GUI HTTPS 200"
else
    echo "[${TIMESTAMP}] FAIL: GUI HTTPS ${HTTP_GUI}"
fi

# 3. Replicas API
REPLICAS_API=$(docker service ls --filter "name=${SERVICE_API}" --format "{{.Replicas}}" 2>/dev/null || echo "N/A")
if [[ "$REPLICAS_API" == "1/1" ]]; then
    echo "[${TIMESTAMP}] OK: API replicas ${REPLICAS_API}"
else
    echo "[${TIMESTAMP}] FAIL: API replicas ${REPLICAS_API}"
fi
EOF

chmod +x ~/relevo-deploy/health-check-relevo.sh

─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

Paso 7: Configurar Backup Automático (Similar a Sherlock)

# Crear script de backup
cat > ~/relevo-deploy/backup-relevo.sh << 'EOF'
#!/bin/bash
set -euo pipefail

BACKUP_DIR="/home/sprintadmin/backups/relevo"
TIMESTAMP=$(date "+%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/relevo_${TIMESTAMP}.db.gz"
DB_PATH="/etc/easypanel/projects/sprintjudicial/relevo-gui/volumes/database/relevo.db"
RETENTION_DAYS=30

mkdir -p "$BACKUP_DIR"
echo "[$(date)] Iniciando backup Relevo..."

# 1. Checkpoint WAL (si está en modo WAL)
sqlite3 "$DB_PATH" "PRAGMA wal_checkpoint(TRUNCATE);" 2>/dev/null || true

# 2. Backup comprimido
gzip -c "$DB_PATH" > "$BACKUP_FILE"

# 3. Verificar tamaño mínimo
FILE_SIZE=$(stat -c%s "$BACKUP_FILE" 2>/dev/null || echo "0")
if [[ "$FILE_SIZE" -lt 100 ]]; then
    echo "[$(date)] ERROR: Backup muy pequeño (${FILE_SIZE} bytes)"
    rm -f "$BACKUP_FILE"
    exit 1
fi
echo "[$(date)] Backup: ${BACKUP_FILE} (${FILE_SIZE} bytes)"

# 4. Retención
DELETED=$(find "$BACKUP_DIR" -name "relevo_*.db.gz" -mtime +"$RETENTION_DAYS" -delete -print | wc -l)
[[ "$DELETED" -gt 0 ]] && echo "[$(date)] ${DELETED} backups antiguos eliminados"

echo "[$(date)] Backup completado"
EOF

chmod +x ~/relevo-deploy/backup-relevo.sh

# Agregar al crontab (2 AM diario)
(crontab -l 2>/dev/null; echo "0 2 * * * ~/relevo-deploy/backup-relevo.sh >> /var/log/relevo-backup.log 2>&1") |
crontab -

─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

Paso 8: Actualizar Documentación del VPS

# Actualizar CLAUDE.md con información de Relevo
# Agregar a la sección "Active Subdominios":
# - `relevo.sprintjudicial.com` - Relevo ausencias GUI (Streamlit)

# Actualizar la sección de servicios con información de Relevo

─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

🔍 Troubleshooting

GUI no conecta con API

# Ver logs de GUI
docker service logs sprintjudicial_relevo-gui --tail 100

# Verificar que API está corriendo
docker service ls | grep relevo-api

# Verificar resolución de nombres desde contenedor GUI
docker exec $(docker ps -q -f "name=relevo-gui") ping -c 2 relevo-api

Error de permisos en base de datos

# Corregir permisos
sudo chown -R 1000:1000 /etc/easypanel/projects/sprintjudicial/relevo-gui/volumes/
sudo chmod -R 755 /etc/easypanel/projects/sprintjudicial/relevo-gui/volumes/

SSL no se genera

# Verificar que Traefik está corriendo
docker service ls | grep traefik

# Forzar regeneración de certificado (EasyPanel > Domain > Re-save)

─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

✅ Lista de Verificación Final

  • [ ] DNS relevo.sprintjudicial.com configurado y propagado
  • [ ] Directorios de volúmenes creados con permisos correctos
  • [ ] Servicio relevo-api creado en EasyPanel (sin dominio)
  • [ ] Servicio relevo-gui creado en EasyPanel (con dominio)
  • [ ] Ambos servicios comparten los mismos volúmenes
  • [ ] SECRET_KEY idéntico en ambos servicios
  • [ ] Servicios Docker muestran 1/1 replicas
  • [ ] GUI accesible via HTTPS: https://relevo.sprintjudicial.com
  • [ ] Comunicación GUI→API funcional (sin errores de conexión)
  • [ ] Base de datos SQLite compartida funciona
  • [ ] Script de health check creado
  • [ ] Script de backup configurado en crontab
  • [ ] CLAUDE.md actualizado con información de Relevo


---


Veo el problema principal: El servicio sprintjudicial_relevo-api está en 0/0 replicas, lo que significa que NO está
corriendo. Solo tienes el servicio GUI creado.

Los logs muestran que el mismo contenedor está intentando ejecutarse en ambos modos (GUI y API), lo que indica que
solo se creó un servicio en EasyPanel.

─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

🔧 Solución: Crear el Servicio API en EasyPanel

Necesitas crear el segundo servicio (relevo-api) en EasyPanel. Sigue estos pasos:

Paso 1: Acceder a EasyPanel

https://panel.sprintjudicial.com

Paso 2: Crear Servicio API

  1. Click en "Create Service" o "New Service"
  2. Configurar:

Basic Settings:

  • Service Name: relevo-api
  • Image: ghcr.io/hammerdev99/relevo:latest
  • Image Tag: latest

Environment Variables:

RELEVO_MODE=api
SECRET_KEY=<misma-clave-que-usaste-en-relevo-gui>
DATABASE_URL=sqlite:////app/data/database/relevo.db
TZ=America/Bogota

Resources:

  • Memory Limit: 256 MB
  • Memory Reservation: 128 MB
  • CPU Limit: 0.5

Volumes (MISMOS que relevo-gui):

Type: Bind
Source: /etc/easypanel/projects/sprintjudicial/relevo-gui/volumes/database
Target: /app/data/database

Type: Bind
Source: /etc/easypanel/projects/sprintjudicial/relevo-gui/volumes/logs
Target: /app/logs

Network:

  • Domain: NO configurar (el API debe ser interno)
  • Port: 8000 (solo interno, sin exposición externa)
  3. Click en "Deploy"

─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

Paso 3: Verificar que Ambos Servicios Estén Corriendo

# Verificar servicios
docker service ls | grep relevo

# Debes ver AMBOS servicios con 1/1 replicas:
# sprintjudicial_relevo-api   1/1
# sprintjudicial_relevo-gui   1/1

─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

Paso 4: Verificar Comunicación

# Verificar que el API responde internamente
docker exec $(docker ps -q -f "name=relevo-api") curl -s http://localhost:8000/
# Respuesta esperada: {"message": "Relevo API v1"}

# Verificar que la GUI puede resolver el nombre del API
docker exec $(docker ps -q -f "name=relevo-gui") wget -qO- http://relevo-api:8000/
# Respuesta esperada: {"message": "Relevo API v1"}

─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

Paso 5: Verificar la GUI Externamente

# Desde tu máquina local
curl -I https://relevo.sprintjudicial.com
# Debe devolver: HTTP/1.1 200 OK

# O abrir en navegador:
https://relevo.sprintjudicial.com

─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

🔍 Si Sigues Teniendo Problemas

Verificar Configuración del Servicio API en EasyPanel:

  1. En EasyPanel, entra al servicio relevo-api
  2. Verifica que RELEVO_MODE=api esté configurado
  3. Verifica que los volúmenes apunten a los mismos directorios que relevo-gui
  4. Verifica que NO tenga dominio configurado

Verificar Logs del API:

# Ver logs del servicio API
docker service logs sprintjudicial_relevo-api --tail 50

# Si el servicio no arranca, ver logs con más detalle
docker service logs sprintjudicial_relevo-api --tail 100 --follow
