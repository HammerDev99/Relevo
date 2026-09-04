# Infraestructura de Despliegue — Relevo

## Estado actual (v8, 2026-09-04)

**Producción activa** en VPS `31.97.146.7` (red Rama Judicial):
- `relevo-api` → FastAPI en puerto 8000 (interno, sin dominio público)
- `relevo-gui` → Streamlit en `relevo.sprintjudicial.com:8501` (HTTPS vía Traefik)
- BD SQLite en volumen bind-mount: `/etc/easypanel/projects/sprintjudicial/relevo-api/volumes/relevo-db-data/relevo.db`

---

## 1. Arquitectura de Servicios Docker

```
Internet → Traefik (HTTPS) → relevo-gui (:8501)
                                   │
                          [red interna Docker]
                                   │
                            relevo-api (:8000)
                                   │
                          [volumen SQLite compartido]
```

- Ambos servicios usan la **misma imagen** Docker; el modo se selecciona con `RELEVO_MODE=api|gui`.
- La GUI **nunca** accede a la BD directamente — solo llama al API vía HTTP.
- `SECRET_KEY` idéntica en ambos servicios (firmado de cookies de sesión).

### Variables de entorno clave

| Variable | api | gui |
|----------|:---:|:---:|
| `RELEVO_MODE` | `api` | `gui` |
| `SECRET_KEY` | ✅ (igual) | ✅ (igual) |
| `DATABASE_URL` | `sqlite:////app/data/database/relevo.db` | igual |
| `APP_ENV` | `production` | — |
| `RELEVO_SEED_PASSWORD` | ✅ (AUDIT-H7) | — |
| `TZ` | `America/Bogota` | `America/Bogota` |

---

## 2. Demo Rápida (Cloudflare Tunnel)

Para pruebas sin servidor:

```powershell
docker compose -f docker-compose.tunnel.yml up
```

Buscar en logs la URL `https://*.trycloudflare.com`.

---

## 3. Desarrollo Local

```powershell
docker-compose -f docker-compose.dev.yml up --build
# API en localhost:8000, GUI en localhost:8501
```

---

## 4. Persistencia (Base de Datos)

- **SQLite 3** — una sola réplica (no escala horizontalmente).
- **Dev local**: `data/database/relevo.db` (en `.gitignore`).
- **VPS**: bind-mount en `/etc/easypanel/projects/.../relevo-db-data/relevo.db`, owner `1000:1000`.
- **Backup**: script `~/relevo-deploy/backup-relevo.sh` en crontab (2 AM diario). Ver Fase 7 en `docs/others/deploy-vps-instructions.md`.

---

## 4.1 Mecanismo de despliegue (v8)

Ambos servicios se construyen desde el **Dockerfile del repositorio** vía
webhook de GitHub. No hay CI: `.github/workflows` no existe en el repo.

| Servicio | Webhook | Origen |
|----------|---------|--------|
| `relevo-gui` | hook `635246930` | Build desde `main` |
| `relevo-api` | hook `674557340` (creado 2026-09-04) | Build desde `main` |

> **Histórico**: hasta el 2026-09-04 `relevo-api` corría desde una imagen
> pre-construida en `ghcr.io/hammerdev99/relevo:latest`, publicada a mano. Esa
> asimetría provocó que el push de `d194208` desplegara solo la GUI y exigiera
> un deploy manual del API. Resuelto al crear su propio webhook.

**Flujo actual**: `git push origin main` → ambos webhooks disparan → EasyPanel
reconstruye cada servicio. Verificar el despliegue con el **digest** del
contenedor (`docker inspect ... --format '{{.Image}}'`), nunca con el tag.

---

## 5. Guías de Referencia

| Tarea | Documento |
|-------|-----------|
| **Actualizar la app ya desplegada (con datos)** | **`docs/others/actualizacion-vps.md`** |
| Despliegue inicial en VPS | `docs/others/deploy-vps-instructions.md` |
| Rotación de logs (logrotate + daemon.json) | `docs/others/deploy-vps-instructions.md` §6 |
| Backup automatizado | `docs/others/deploy-vps-instructions.md` §7 |
| Acciones operativas manuales | `docs/plannings/PLAN_08_*.md` §9 |
