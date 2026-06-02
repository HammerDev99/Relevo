# SPRINT_16 — Despliegue VPS Productivo + Calendario Interactivo

| Campo | Valor |
|-------|-------|
| **Fecha** | 2026-06-02 |
| **Fase CDAID** | Deploy + Feature |
| **Milestone** | v6 |
| **SPECs** | SPEC-S15-C5, SPEC-S15-C6, fix-perfil, fix-healthcheck |
| **Estado** | ✅ Done |

---

## 1. Contexto

Este sprint cierra el Milestone v6 (despliegue productivo) y completa los dos ítems diferidos de PLAN_07 (tooltip de grupos e interactividad del calendario).

---

## 2. Trabajo realizado

### 2.1 Auditoría y correcciones pre-despliegue

| ID | Hallazgo | Corrección | Archivos |
|----|----------|-----------|---------|
| FIX-01 | HEALTHCHECK del Dockerfile solo chequeaba `:8000`; el contenedor `relevo-gui` corre en `:8501` → loop de reinicios | Script modo-consciente `docker-healthcheck.sh` | `Dockerfile`, `docker-healthcheck.sh` |
| FIX-02 | `04_perfil.py` definía `show()` pero nunca la invocaba → página de perfil en blanco | Agregar `if __name__ == "__main__": show()` | `src/app/gui/pages/04_perfil.py` |
| FIX-03 | Sin guía unificada para Claude del VPS | Documento `deploy-vps-instructions.md` con todas las fases | `docs/others/deploy-vps-instructions.md` |

### 2.2 Despliegue productivo (Milestone v6)

- Migración de BD de producción local → VPS vía SCP + `sudo mv`
- Configuración de volúmenes bind mount en EasyPanel (`relevo-api/volumes/relevo-db-data`)
- Verificación de `relevo-api` y `relevo-gui` con `1/1` réplicas y healthcheck `healthy`
- Login funcional con datos reales de producción

### 2.3 SPEC-S15-C5: Tooltip de grupos en calendario

**Backend:**
- `ConfiguracionApp` — modelo singleton con `mostrar_grupos_tooltip: bool` (default `True`)
- `seed.py` — inicializa `ConfiguracionApp(id=1)` de forma idempotente
- `schemas/configuracion.py` — `ConfiguracionRead` + `ConfiguracionUpdate`
- `routes/configuracion.py` — `GET /configuracion` (público) + `PATCH /configuracion` (solo coordinador)
- `main.py` — registra el nuevo router
- `schemas/disponibilidad.py` — añade `grupos_ausentes: list[str]`
- `routes/disponibilidad.py` — carga grupos ausentes con `selectinload` (sin N+1 queries)

**Frontend:**
- `03_coordinacion.py` — nueva tab "⚙️ Configuración" con `st.toggle` para activar/desactivar tooltip
- `gui/services/coordinacion_service.py` — métodos `obtener_configuracion()` y `actualizar_configuracion()`
- `02_disponibilidad.py` — tooltip HTML `title` en cada celda hábil con nombres de grupos (respeta RN5: no expone nombres de empleados)

### 2.4 SPEC-S15-C6: Calendario interactivo

- Botón `→` por cada celda hábil del calendario
- Al hacer clic: guarda `fecha_preseleccionada` y `detalle_fecha` en `session_state`
- Panel de detalle debajo del calendario: estado del día + grupos ausentes + botón "📝 Crear Solicitud para este día"
- `st.switch_page("pages/01_solicitudes.py")` navega a solicitudes con fecha pre-cargada
- `01_solicitudes.py` lee `fecha_preseleccionada`, auto-expande el formulario y pre-popula `f_inicio`

---

## 3. Archivos modificados / creados

| Archivo | Tipo | Cambio |
|---------|------|--------|
| `Dockerfile` | mod | HEALTHCHECK modo-consciente |
| `docker-healthcheck.sh` | nuevo | Script healthcheck api/gui |
| `docs/others/deploy-vps-instructions.md` | nuevo | Guía completa despliegue VPS |
| `src/app/models.py` | mod | `ConfiguracionApp` singleton |
| `src/app/seed.py` | mod | Inicializa `ConfiguracionApp` |
| `src/app/schemas/configuracion.py` | nuevo | DTOs de configuración |
| `src/app/routes/configuracion.py` | nuevo | Endpoints GET/PATCH `/configuracion` |
| `src/app/main.py` | mod | Registra router configuracion |
| `src/app/schemas/disponibilidad.py` | mod | `grupos_ausentes: list[str]` |
| `src/app/routes/disponibilidad.py` | mod | `selectinload` + grupos ausentes |
| `src/app/gui/services/coordinacion_service.py` | mod | Métodos config |
| `src/app/gui/pages/02_disponibilidad.py` | mod | Tooltip + interactividad (C5+C6) |
| `src/app/gui/pages/03_coordinacion.py` | mod | Tab configuración + toggle |
| `src/app/gui/pages/04_perfil.py` | mod | `show()` call faltante |
| `src/app/gui/pages/01_solicitudes.py` | mod | Fecha pre-cargada desde calendario |

---

## 4. Verificación

| Herramienta | Resultado |
|-------------|-----------|
| `pytest -x` | ✅ 54 passed |
| `ruff check src` | ✅ All checks passed |
| Despliegue VPS | ✅ Ambos servicios `1/1` healthy |
| Login con datos prod | ✅ Funcional |

---

## 5. Mejoras y fixes post-sprint (misma sesión)

| Commit | Tipo | Descripción |
|--------|------|-------------|
| `5a62c78` | chore | `.gitignore` + `CREDENCIALES_PRUEBA.md` (credenciales locales fuera del repo) |
| `621cab1` | chore | Eliminar credenciales de prueba del README público |
| `2b07f88` | fix | `session_state.pop()` para limpiar campos de contraseña; deshabilitar `/docs` en producción (`APP_ENV=production`) |
| `18feda5` | fix | Deshabilitar botón `→` del calendario visualmente (lógica C6 preservada en comentarios) |
| `15c57b1` | feat | Disponibilidad pública sin login + `require_auth()` en páginas protegidas; login en sidebar |
| `59875bc` | feat | UX móvil calendario: CSS Grid nativo, celdas responsivas, leyenda compacta, `selectbox` año |
| `9c2a80c` | feat | Navegación mes/año con botones `−`/`+` y `‹`/`›` en lugar de selectbox |
| `0c5ea39` | feat | Coordinadores LUISA y JOHN añadidos al seed (patrón `nombre@test.com` / `nombre123`) |
| `9ed81a3` | fix | Label mes/año sincronizado con estado antes de renderizar; botones con color neutro |

---

## 6. Pendientes diferidos → PLAN_08

| ID | Hallazgo | Razón |
|----|----------|-------|
| SPEC-S15-D5 | Rotación de logs en VPS | Configuración `logrotate` en host |
| SPEC-S15-D6 | Script de backup automatizado en crontab | Ejecución manual en VPS pendiente |
