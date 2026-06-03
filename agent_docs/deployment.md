# Infraestructura de Despliegue — Relevo

## Estado actual (v7, 2026-06-02)

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

## 5. Guías de Referencia

| Tarea | Documento |
|-------|-----------|
| Despliegue inicial en VPS | `docs/others/deploy-vps-instructions.md` |
| Rotación de logs (logrotate + daemon.json) | `docs/others/deploy-vps-instructions.md` §6 |
| Backup automatizado | `docs/others/deploy-vps-instructions.md` §7 |
| Acciones operativas manuales | `docs/plannings/PLAN_08_*.md` §9 |
