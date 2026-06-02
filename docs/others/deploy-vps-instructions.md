# Instrucciones de Despliegue VPS — Relevo
> Documento para Claude (agente en VPS). Ejecutar en orden estricto.

## Contexto del sistema

- **App**: Sistema de gestión de ausencias (vacaciones/permisos), 10 empleados, dependencia judicial Colombia
- **Arquitectura**: Una sola imagen Docker con dos modos via `RELEVO_MODE=api|gui`
  - `relevo-api`: FastAPI en puerto 8000 (sin dominio público)
  - `relevo-gui`: Streamlit en puerto 8501 (dominio `relevo.sprintjudicial.com`)
- **BD**: SQLite en volumen compartido — solo el API escribe, la GUI llama al API vía HTTP
- **Repo**: `https://github.com/HammerDev99/Relevo.git` (rama `main`)
- **Panel**: EasyPanel en `https://panel.sprintjudicial.com`
- **VPS**: `31.97.146.7`, usuario `sprintadmin`

---

## Fase 1 — Preparar VPS (SSH)

```bash
ssh sprintadmin@31.97.146.7
```

### 1.1 Crear directorios de volúmenes

```bash
# Directorios para volúmenes bind mount
sudo mkdir -p /etc/easypanel/projects/sprintjudicial/relevo-api/volumes/database
sudo mkdir -p /etc/easypanel/projects/sprintjudicial/relevo-api/volumes/logs

# Permisos para UID 1000 (usuario relevo dentro del contenedor)
sudo chown -R 1000:1000 /etc/easypanel/projects/sprintjudicial/relevo-api/volumes/
sudo chmod -R 755 /etc/easypanel/projects/sprintjudicial/relevo-api/volumes/

# Verificar
ls -la /etc/easypanel/projects/sprintjudicial/relevo-api/volumes/
```

### 1.2 Verificar DNS

```bash
# Debe resolver a 31.97.146.7
dig relevo.sprintjudicial.com +short
nslookup relevo.sprintjudicial.com
```

Si el DNS no resuelve todavía, crear registro A:
- Nombre: `relevo`
- Valor: `31.97.146.7`
- TTL: 3600

---

## Fase 2 — Migrar base de datos de producción

La BD de producción (`relevo.db`) viene desde la máquina del desarrollador.

### 2.1 Desde la máquina local (Windows), ejecutar:

```powershell
# Copiar BD de producción al VPS
scp C:\Desarrollo\RamaJudicial\Relevo\data\database\relevo.db `
    sprintadmin@31.97.146.7:/etc/easypanel/projects/sprintjudicial/relevo-api/volumes/database/relevo.db
```

### 2.2 En el VPS, verificar y corregir permisos:

```bash
# Verificar que llegó y tiene tamaño razonable
ls -lh /etc/easypanel/projects/sprintjudicial/relevo-api/volumes/database/relevo.db

# Corregir ownership
sudo chown 1000:1000 /etc/easypanel/projects/sprintjudicial/relevo-api/volumes/database/relevo.db

# Verificar tablas (requiere sqlite3)
sqlite3 /etc/easypanel/projects/sprintjudicial/relevo-api/volumes/database/relevo.db \
    "SELECT name FROM sqlite_master WHERE type='table';"
# Debe listar: empleados, grupos, empleado_grupo, solicitudes
```

---

## Fase 3 — Crear servicios en EasyPanel

Acceder a: `https://panel.sprintjudicial.com`

### 3.1 Crear servicio `relevo-api` (PRIMERO)

**Build Settings:**
- Type: **App** (construir desde GitHub)
- Repository: `https://github.com/HammerDev99/Relevo.git`
- Branch: `main`
- Build Method: **Dockerfile** (usa el Dockerfile en la raíz)
- Service Name: `relevo-api`

**Environment Variables:**
```
RELEVO_MODE=api
SECRET_KEY=<generar con: openssl rand -hex 32>
DATABASE_URL=sqlite:////app/data/database/relevo.db
TZ=America/Bogota
```

**Volumes (Bind Mounts):**
| Host Path | Container Path |
|-----------|---------------|
| `/etc/easypanel/projects/sprintjudicial/relevo-api/volumes/database` | `/app/data/database` |
| `/etc/easypanel/projects/sprintjudicial/relevo-api/volumes/logs` | `/app/logs` |

**Network:**
- Port: `8000`
- **NO configurar dominio** (API es interna)

**Resources:**
- Memory Limit: 256 MB
- Memory Reservation: 128 MB
- CPU Limit: 0.5

→ Click **Deploy** y esperar a que el healthcheck muestre `healthy`.

**Verificar:**
```bash
# En el VPS
docker service ls | grep relevo-api
# Debe mostrar: sprintjudicial_relevo-api   1/1

# Health del API
docker exec $(docker ps -q -f "name=relevo-api") curl -s http://localhost:8000/
# Respuesta: {"message": "Relevo API v1"}
```

---

### 3.2 Crear servicio `relevo-gui` (DESPUÉS de que relevo-api esté healthy)

**Build Settings:**
- Type: **App** (mismo repo)
- Repository: `https://github.com/HammerDev99/Relevo.git`
- Branch: `main`
- Build Method: **Dockerfile**
- Service Name: `relevo-gui`

**Environment Variables:**
```
RELEVO_MODE=gui
SECRET_KEY=<MISMA clave que relevo-api>
DATABASE_URL=sqlite:////app/data/database/relevo.db
TZ=America/Bogota
```

**Volumes (Bind Mounts — MISMOS PATHS que relevo-api):**
| Host Path | Container Path |
|-----------|---------------|
| `/etc/easypanel/projects/sprintjudicial/relevo-api/volumes/database` | `/app/data/database` |
| `/etc/easypanel/projects/sprintjudicial/relevo-api/volumes/logs` | `/app/logs` |

> ⚠️ Los paths del host son LOS MISMOS que en relevo-api. Así comparten la BD.

**Network:**
- Port: `8501`
- Domain: `relevo.sprintjudicial.com`
- HTTPS: Habilitado (Let's Encrypt automático)

**Resources:**
- Memory Limit: 512 MB
- Memory Reservation: 256 MB
- CPU Limit: 0.5

→ Click **Deploy** y esperar a que el healthcheck muestre `healthy`.

---

## Fase 4 — Verificación completa

```bash
# 1. Ambos servicios corriendo
docker service ls | grep relevo
# sprintjudicial_relevo-api   1/1
# sprintjudicial_relevo-gui   1/1

# 2. API responde internamente
docker exec $(docker ps -q -f "name=relevo-api") curl -s http://localhost:8000/

# 3. GUI puede resolver y llamar al API
docker exec $(docker ps -q -f "name=relevo-gui") \
    wget -qO- http://relevo-api:8000/

# 4. HTTPS externo
curl -I https://relevo.sprintjudicial.com
# Esperado: HTTP/2 200

# 5. Datos de producción intactos
sqlite3 /etc/easypanel/projects/sprintjudicial/relevo-api/volumes/database/relevo.db \
    "SELECT nombre, rol FROM empleados;"
```

---

## Fase 5 — Backup automático

```bash
mkdir -p ~/relevo-deploy

cat > ~/relevo-deploy/backup-relevo.sh << 'EOF'
#!/bin/bash
set -euo pipefail

BACKUP_DIR="/home/sprintadmin/backups/relevo"
TIMESTAMP=$(date "+%Y%m%d_%H%M%S")
DB_PATH="/etc/easypanel/projects/sprintjudicial/relevo-api/volumes/database/relevo.db"
BACKUP_FILE="${BACKUP_DIR}/relevo_${TIMESTAMP}.db.gz"
RETENTION_DAYS=30

mkdir -p "$BACKUP_DIR"
echo "[$(date)] Iniciando backup Relevo..."

sqlite3 "$DB_PATH" "PRAGMA wal_checkpoint(TRUNCATE);" 2>/dev/null || true
gzip -c "$DB_PATH" > "$BACKUP_FILE"

FILE_SIZE=$(stat -c%s "$BACKUP_FILE" 2>/dev/null || echo "0")
if [[ "$FILE_SIZE" -lt 100 ]]; then
    echo "[$(date)] ERROR: Backup muy pequeño (${FILE_SIZE} bytes)"
    rm -f "$BACKUP_FILE"
    exit 1
fi
echo "[$(date)] OK: ${BACKUP_FILE} (${FILE_SIZE} bytes)"

DELETED=$(find "$BACKUP_DIR" -name "relevo_*.db.gz" -mtime +"$RETENTION_DAYS" -delete -print | wc -l)
[[ "$DELETED" -gt 0 ]] && echo "[$(date)] ${DELETED} backups antiguos eliminados"
EOF

chmod +x ~/relevo-deploy/backup-relevo.sh

# Crontab: backup diario a las 2 AM
(crontab -l 2>/dev/null; echo "0 2 * * * ~/relevo-deploy/backup-relevo.sh >> /var/log/relevo-backup.log 2>&1") | crontab -
```

---

## Troubleshooting

### GUI no conecta con API
```bash
# Ver logs de GUI
docker service logs sprintjudicial_relevo-gui --tail 100

# Verificar resolución de nombre desde GUI
docker exec $(docker ps -q -f "name=relevo-gui") \
    wget -qO- http://relevo-api:8000/ || echo "FALLO conexion"

# El API debe estar en la misma red Docker
docker network inspect $(docker network ls -q -f "name=sprintjudicial") | grep -A5 relevo
```

### Healthcheck falla en GUI (loop de reinicios)
```bash
# Verificar que RELEVO_MODE=gui está configurado en el servicio
docker service inspect sprintjudicial_relevo-gui | grep RELEVO_MODE

# Probar healthcheck endpoint de Streamlit
docker exec $(docker ps -q -f "name=relevo-gui") \
    curl -f http://localhost:8501/_stcore/health
```

### Permisos de BD
```bash
sudo chown -R 1000:1000 /etc/easypanel/projects/sprintjudicial/relevo-api/volumes/
sudo chmod -R 755 /etc/easypanel/projects/sprintjudicial/relevo-api/volumes/
```

### SSL no se genera
```bash
# Verificar Traefik
docker service ls | grep traefik
# En EasyPanel: Domain → Re-save para forzar regeneración
```

---

## Lista de verificación final

- [ ] DNS `relevo.sprintjudicial.com` → `31.97.146.7` propagado
- [ ] Directorios de volúmenes creados y con permisos `1000:1000`
- [ ] BD de producción copiada al VPS (`relevo.db`)
- [ ] `relevo-api` creado, `1/1 replicas`, sin dominio
- [ ] `relevo-gui` creado, `1/1 replicas`, con dominio `relevo.sprintjudicial.com`
- [ ] Ambos servicios usan la MISMA `SECRET_KEY`
- [ ] Ambos servicios montan los MISMOS paths de volumen del host
- [ ] `curl https://relevo.sprintjudicial.com` responde `200`
- [ ] Login funcional con datos de producción
- [ ] Script de backup configurado en crontab
