# Procedimiento de Actualización — Relevo en VPS (producción con datos)

> **Uso**: actualizar la aplicación desplegada sin perder datos de producción.
> Distinto de `deploy-vps-instructions.md`, que cubre el despliegue **inicial**.
>
> Verificado el 2026-09-04 contra el VPS real (`31.97.146.7`).

---

## 0. Contexto verificado

| Elemento | Valor |
|----------|-------|
| VPS | `31.97.146.7`, usuario `sprintadmin` |
| Panel | `https://panel.sprintjudicial.com` |
| GUI pública | `https://relevo.sprintjudicial.com` |
| Repo | `https://github.com/HammerDev99/Relevo.git` (rama `main`) |
| **Ruta real de la BD** | `/etc/easypanel/projects/sprintjudicial/relevo-api/volumes/relevo-db-data/relevo.db` |

### Asimetría de despliegue (hallazgo 2026-09-04)

Los dos servicios se actualizan por **mecanismos distintos**:

| Servicio | Imagen | Mecanismo |
|----------|--------|-----------|
| `relevo-gui` | `easypanel/sprintjudicial/relevo-gui` | Build desde Dockerfile en EasyPanel |
| `relevo-api` | `ghcr.io/hammerdev99/relevo:latest` | **Imagen pre-construida en GHCR** |

**No existe `.github/workflows` en el repositorio** — verificado en el working tree, en todo el historial (`git log --all`) y en `origin/main`. La imagen de GHCR se publicó manualmente. Las variables `GIT_SHA` / `DEPLOY_TIMESTAMP` del servicio son remanentes de un pipeline que nunca se materializó (`GIT_SHA=undefined` en `relevo-api`).

**Consecuencia**: `git push` + *Deploy* **no actualiza `relevo-api`**. EasyPanel solo puede volver a hacer `pull` del mismo tag `:latest`, y Docker Swarm no repite el pull de un tag sin cambios sin forzarlo.

La **Fase 4** de este documento resuelve la asimetría de forma permanente.

---

## 1. Qué NO se ve afectado por una actualización

La base de datos vive **fuera** del contenedor, en un bind-mount del host:

```
Host VPS:    /etc/easypanel/.../relevo-db-data/relevo.db
                      │  bind-mount
Contenedor:  /app/data/database/relevo.db
```

Reconstruir o reemplazar la imagen sustituye únicamente el **código**. El contenedor se destruye y se crea otro; el archivo `.db` permanece intacto en el disco del host.

**Además**: el milestone v8 no trae migración de esquema. Ninguna tabla ni columna cambia, por lo que la BD es compatible con el código nuevo y con el anterior (rollback sin pérdida).

---

## Fase 1 — Preparación y respaldo (SSH)

```bash
ssh sprintadmin@31.97.146.7
```

### 1.1 Confirmar la ruta real de la BD

Fuente de verdad: lo que el contenedor monta ahora mismo.

```bash
docker inspect $(docker ps -q -f "name=relevo-api") \
  --format '{{range .Mounts}}{{.Source}} -> {{.Destination}}{{"\n"}}{{end}}'
```

Tomar el `Source` que apunta a `/app/data/database` y fijarlo:

```bash
DB="/etc/easypanel/projects/sprintjudicial/relevo-api/volumes/relevo-db-data/relevo.db"
ls -lh "$DB"
sqlite3 "$DB" "SELECT COUNT(*) AS empleados FROM empleados; SELECT COUNT(*) AS solicitudes FROM solicitudes;"
```

> Si la ruta que devuelve `docker inspect` no coincide con la de arriba, **usar la que devuelve el comando** y avisar para corregir la documentación.

### 1.2 Backup verificado

```bash
mkdir -p ~/backups/relevo
STAMP=$(date +%Y%m%d_%H%M%S)

# .backup es consistente aunque haya escrituras en curso (mejor que gzip directo)
sqlite3 "$DB" "PRAGMA wal_checkpoint(TRUNCATE);" 2>/dev/null || true
sqlite3 "$DB" ".backup '/home/sprintadmin/backups/relevo/pre_v8_${STAMP}.db'"
gzip -c ~/backups/relevo/pre_v8_${STAMP}.db > ~/backups/relevo/pre_v8_${STAMP}.db.gz

echo "STAMP=$STAMP"   # anotar este valor: lo necesita el rollback
```

**Verificar que el backup es restaurable** (un backup sin verificar no es un backup):

```bash
zcat ~/backups/relevo/pre_v8_${STAMP}.db.gz > /tmp/verify.db
sqlite3 /tmp/verify.db "PRAGMA integrity_check;"
sqlite3 /tmp/verify.db "SELECT COUNT(*) FROM empleados;"
rm /tmp/verify.db
```

Debe imprimir `ok` y el mismo número de empleados que el paso 1.1.

### 1.3 Registrar el estado previo

```bash
{
  echo "=== EMPLEADOS Y GRUPOS ==="
  sqlite3 "$DB" "SELECT e.id, e.nombre, e.rol, COALESCE(GROUP_CONCAT(g.nombre),'(sin grupo)') FROM empleados e LEFT JOIN empleado_grupo eg ON eg.empleado_id=e.id LEFT JOIN grupos g ON g.id=eg.grupo_id GROUP BY e.id ORDER BY e.id;"
  echo "=== GRUPOS ==="
  sqlite3 "$DB" "SELECT nombre, min_presentes FROM grupos ORDER BY nombre;"
  echo "=== CONTEOS ==="
  sqlite3 "$DB" "SELECT 'empleados', COUNT(*) FROM empleados UNION ALL SELECT 'solicitudes', COUNT(*) FROM solicitudes;"
} > ~/estado_pre_v8.txt

cat ~/estado_pre_v8.txt
```

### 1.4 Registrar la versión desplegada (para comprobar que el deploy surtió efecto)

> **Importante**: `ContainerSpec.Image` devuelve solo el tag (`...:latest`), que **nunca cambia** entre despliegues. Comparar ese valor daría "no cambió" incluso en un deploy exitoso. Hay que registrar el **digest** de la imagen que el contenedor está corriendo.

```bash
# Tag (informativo)
docker service inspect sprintjudicial_relevo-api \
  --format '{{.Spec.TaskTemplate.ContainerSpec.Image}}' > ~/imagen_pre_v8.txt

# Digest real de la imagen en ejecución — este es el que debe cambiar
docker inspect $(docker ps -q -f "name=relevo-api") \
  --format '{{.Image}}' > ~/digest_pre_v8.txt

cat ~/imagen_pre_v8.txt ~/digest_pre_v8.txt
```

---

## Fase 2 — Publicar el código (máquina local)

```powershell
cd C:\Desarrollo\RamaJudicial\Relevo

# Confirmar que todo está verde antes de publicar
.venv\Scripts\python.exe -m pytest
.venv\Scripts\python.exe -m ruff check src tests scripts

git log --oneline origin/main..HEAD    # revisar qué se va a publicar
git push origin main
```

---

## Fase 3 — Desplegar `relevo-gui`

`relevo-gui` sí construye desde el Dockerfile, así que se actualiza con el flujo normal.

1. EasyPanel → servicio **`relevo-gui`** → **Deploy**.
2. Esperar a que el servicio quede `healthy`.

**No modificar** variables de entorno ni volúmenes. En particular, `SECRET_KEY` debe seguir siendo **idéntica** en ambos servicios: si cambia, se invalidan todas las sesiones activas.

---

## Fase 4 — Actualizar `relevo-api`

Elegir **una** de las dos vías.

### Opción A (recomendada) — Migrar a build-from-Dockerfile

Elimina la dependencia de GHCR y la asimetría entre servicios. Se configura una sola vez; después, las actualizaciones son *push* + *Deploy* en ambos servicios.

En EasyPanel → servicio **`relevo-api`** → **Source / Build**:

1. Cambiar el origen de **Docker Image** a **App / GitHub**:
   - Repository: `https://github.com/HammerDev99/Relevo.git`
   - Branch: `main`
   - Build Method: **Dockerfile** (raíz del repo)
2. **Conservar sin cambios**:
   - Environment: `RELEVO_MODE=api`, `SECRET_KEY` (la misma que la GUI), `DATABASE_URL=sqlite:////app/data/database/relevo.db`, `TZ=America/Bogota`
   - Volumes: `/etc/easypanel/projects/sprintjudicial/relevo-api/volumes/relevo-db-data` → `/app/data/database`, y el de logs → `/app/logs`
   - Port `8000`, **sin dominio** (el API es interno)
   - Resources: 256 MB límite / 128 MB reserva / 0.5 CPU
3. **Deploy** y esperar `healthy`.

> El mismo Dockerfile sirve para ambos servicios: el modo lo decide `RELEVO_MODE`, no la imagen.

### Opción B — Publicar la imagen a GHCR manualmente

Mantiene el esquema actual. Requiere Docker local y acceso de escritura a GHCR.

```powershell
# En la máquina local
docker build -t ghcr.io/hammerdev99/relevo:latest .
docker push ghcr.io/hammerdev99/relevo:latest
```

```bash
# En el VPS: forzar el pull (sin --force el tag :latest puede no refrescarse)
docker service update --image ghcr.io/hammerdev99/relevo:latest --force sprintjudicial_relevo-api
```

---

## Fase 5 — Verificación

### 5.1 Servicios arriba

```bash
docker service ls | grep relevo     # ambos deben mostrar 1/1
```

### 5.2 El código nuevo está corriendo

El **digest** de la imagen en ejecución debe haber cambiado respecto a la Fase 1.4. Comparar el tag no sirve: con `:latest` es siempre el mismo.

```bash
DIGEST_POST=$(docker inspect $(docker ps -q -f "name=relevo-api") --format '{{.Image}}')
echo "pre : $(cat ~/digest_pre_v8.txt)"
echo "post: ${DIGEST_POST}"

if [ "$(cat ~/digest_pre_v8.txt)" = "${DIGEST_POST}" ]; then
  echo "AVISO: el digest NO cambió — el deploy no surtió efecto"
else
  echo "OK: la imagen en ejecución cambió"
fi
```

Si el digest no cambió con la Opción B, Swarm reutilizó el `:latest` en caché: repetir con `docker service update --image ghcr.io/hammerdev99/relevo:latest --force sprintjudicial_relevo-api`.

### 5.3 El endpoint nuevo existe

> La ruta `/coordinacion/usuarios` **ya existía** antes de esta versión: la sirve el `GET` de listado. Verificar por **método**, no por ruta — lo nuevo es `post`.
> `PATCH` y `DELETE` viven en otra ruta (`/coordinacion/usuarios/{usuario_id}`), por eso no aparecen en este listado.

```bash
docker exec $(docker ps -q -f "name=relevo-api") \
  curl -s http://localhost:8000/openapi.json \
  | python3 -c "import json,sys; print(sorted(json.load(sys.stdin)['paths']['/coordinacion/usuarios'].keys()))"
```

- Antes: `['get']`
- **Después**: `['get', 'post']` ← verificado contra el OpenAPI que genera el código nuevo

### 5.4 Datos intactos

```bash
{
  echo "=== EMPLEADOS Y GRUPOS ==="
  sqlite3 "$DB" "SELECT e.id, e.nombre, e.rol, COALESCE(GROUP_CONCAT(g.nombre),'(sin grupo)') FROM empleados e LEFT JOIN empleado_grupo eg ON eg.empleado_id=e.id LEFT JOIN grupos g ON g.id=eg.grupo_id GROUP BY e.id ORDER BY e.id;"
  echo "=== GRUPOS ==="
  sqlite3 "$DB" "SELECT nombre, min_presentes FROM grupos ORDER BY nombre;"
  echo "=== CONTEOS ==="
  sqlite3 "$DB" "SELECT 'empleados', COUNT(*) FROM empleados UNION ALL SELECT 'solicitudes', COUNT(*) FROM solicitudes;"
} > ~/estado_post_v8.txt

diff ~/estado_pre_v8.txt ~/estado_post_v8.txt && echo "SIN CAMBIOS — correcto"
```

A partir de SPEC-S18-C1 el seed ya no reescribe grupos ni `min_presentes`, así que el `diff` **debe salir limpio**. Si muestra diferencias, revisar los logs del API:

```bash
docker service logs sprintjudicial_relevo-api --tail 50
```

> **Esta es la prueba decisiva del fix.** El estado capturado en la Fase 1.3 el 2026-09-04 mostraba *drift* real respecto al seed: YESENIA, FLOR y DANIEL estaban en G2/G2/G3, mientras el `empleados_mapping` los tiene en G3/G1/G2. Alguien los reasignó desde el panel de Coordinación.
>
> Con el bug anterior, este reinicio los habría devuelto a G3/G1/G2 — pérdida silenciosa. Con SPEC-S18-C1 deben **conservar** G2/G2/G3.
>
> Si el `diff` muestra que esos tres volvieron a los valores del seed, el fix no está desplegado: revisar la Fase 5.2 (el digest no cambió).

### 5.5 Los tres usuarios creados por consola siguen ahí

```bash
sqlite3 "$DB" "SELECT nombre, rol, activo FROM empleados WHERE correo IN ('danielrevollo@test.com','mariana@test.com','rosa@test.com');"
```

### 5.6 Verificación funcional (navegador)

En `https://relevo.sprintjudicial.com`, con sesión de coordinación:

- [ ] *Coordinación → Personal de la Oficina* muestra **➕ Registrar Nuevo Empleado**
- [ ] Crear un empleado de prueba → aparece en el listado
- [ ] Reintentar con el mismo correo → error claro de duplicado (no error 500)
- [ ] Eliminar el empleado de prueba
- [ ] *Disponibilidad* → hover sobre un día ocupado → muestra **nombres** de ausentes
- [ ] El hover **no** muestra el motivo ni el tipo de la ausencia

---

## Fase 6 — Rollback

### 6.1 Solo código (lo habitual)

- **Opción A**: EasyPanel → `relevo-api` → *Deployments* → **Redeploy** de la versión anterior.
- **Opción B**: `docker service update --image ghcr.io/hammerdev99/relevo:<tag-anterior> --force sprintjudicial_relevo-api`

Como no hay cambio de esquema, la BD actual funciona con el código anterior sin tocar nada.

### 6.2 Datos (solo si fuera necesario)

```bash
# Detener el API primero: evita escrituras durante la restauración
docker service scale sprintjudicial_relevo-api=0

zcat ~/backups/relevo/pre_v8_<STAMP>.db.gz > "$DB"
chown 1000:1000 "$DB"

docker service scale sprintjudicial_relevo-api=1
```

---

## Fase 7 — Post-despliegue

- [ ] **Rotar la contraseña de coordinación** (`admin123`) desde *Mi Perfil → Cambiar Contraseña*. Deuda P0 vencida desde v6; esta versión pone el alta de usuarios detrás de esa contraseña.
- [ ] **Avisar a la oficina**: desde esta versión, cualquier empleado autenticado ve los **nombres** de quienes están ausentes en el calendario (RN5 reformulada en PLAN_09). Borrador en `docs/others/comunicacion_empleados.md`.
- [ ] Actualizar `CREDENCIALES_PRUEBA.md` si se rotaron contraseñas.
- [ ] Confirmar el backup automático: `crontab -l | grep relevo`

---

## Resumen ejecutable

```bash
# ── VPS: preparación ──────────────────────────────────────────
ssh sprintadmin@31.97.146.7
DB="/etc/easypanel/projects/sprintjudicial/relevo-api/volumes/relevo-db-data/relevo.db"
docker inspect $(docker ps -q -f "name=relevo-api") --format '{{range .Mounts}}{{.Source}} -> {{.Destination}}{{"\n"}}{{end}}'   # confirmar ruta
STAMP=$(date +%Y%m%d_%H%M%S) && mkdir -p ~/backups/relevo
sqlite3 "$DB" ".backup '/home/sprintadmin/backups/relevo/pre_v8_${STAMP}.db'"
gzip -c ~/backups/relevo/pre_v8_${STAMP}.db > ~/backups/relevo/pre_v8_${STAMP}.db.gz
zcat ~/backups/relevo/pre_v8_${STAMP}.db.gz > /tmp/v.db && sqlite3 /tmp/v.db "PRAGMA integrity_check;" && rm /tmp/v.db
docker inspect $(docker ps -q -f "name=relevo-api") --format '{{.Image}}' > ~/digest_pre_v8.txt   # digest, no tag
```

```powershell
# ── Local: publicar ───────────────────────────────────────────
.venv\Scripts\python.exe -m pytest && git push origin main
```

```
# ── EasyPanel ─────────────────────────────────────────────────
relevo-gui  → Deploy
relevo-api  → Fase 4 (migrar a Dockerfile, o publicar imagen a GHCR)
```

```bash
# ── VPS: verificar ────────────────────────────────────────────
docker service ls | grep relevo
docker exec $(docker ps -q -f "name=relevo-api") curl -s http://localhost:8000/openapi.json \
  | python3 -c "import json,sys; print(sorted(json.load(sys.stdin)['paths']['/coordinacion/usuarios'].keys()))"
diff ~/estado_pre_v8.txt ~/estado_post_v8.txt
```
