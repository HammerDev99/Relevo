# Relevo — Sistema de gestión de ausencias (dependencia judicial, Colombia)

MVP para coordinar vacaciones y permisos de 10 empleados, con cupos de concurrencia y privacidad. App web Python desplegada en VPS propio (dominio autorizado en la red de la Rama Judicial).

## Reglas críticas (6)

1. **Inmutabilidad**: modelos de dominio y DTOs preferiblemente inmutables. Modelos de persistencia (SQLAlchemy 2.0) con tipado estricto `Mapped`.
2. **Errores**: usar `Result[T, E]` (`Success`/`Failure`), no `try/except` anidados ni excepciones para flujo de control en lógica de negocio.
3. **Logging**: `get_logger(__name__)`, nunca `logging.getLogger` directo.
4. **Privacidad (RN5)**: el **motivo/justificación y el tipo** de ausencia jamás se exponen a terceros. Los **nombres** de ausentes son visibles solo para usuarios **autenticados** (PLAN_09, 2026-09-04). La capa **sin sesión** de `/disponibilidad` solo ve estados derivados (`DISPONIBLE`/`OCUPADO`/`EXCEPCIONAL`) y nombres de grupo.
5. **Arquitectura**: Separación clara entre `src/relevo` (festivos), `src/app/models` (persistencia), `src/app/domain` (reglas de negocio) y `src/app/routes` (FastAPI).
6. **Verificación**: todo cambio pasa `pytest -x` + `ruff check`. Tests cubren Success y Failure.

## Reglas de negocio (contrato)

| ID | Regla |
|----|-------|
| RN2 | 22 días vacaciones/año, 3 días permiso/mes por empleado |
| RN3 | Concurrencia **por grupo**: máx `cupo_normal = miembros_activos − min_presentes` ausentes simultáneos en el grupo |
| RN4 | Excepción **por grupo**: hasta `cupo_normal + 1` ausentes; solo permiso con justificación (no vacaciones como excepción) |
| RN5 | Privacidad: el motivo y el tipo nunca se exponen. Los nombres de ausentes solo se muestran a usuarios autenticados (reformulada en PLAN_09) |
| RN6 | Respaldo: acordar cobertura con un compañero antes de pedir permiso |
| RN7 | Festivos de Colombia (Ley Emiliani) + días hábiles reales |

> **Nota**: El modelo global de v1 ("máx 1/máx 2 en toda la oficina") fue reemplazado en v3 (PLAN_05) por el modelo por grupo. La fuente autoritativa es `src/app/domain.py::validar_solicitud`. Ver `agent_docs/reglas_concurrencia.md`.

## Stack Tecnológico (v1)

| Capa | Tecnología |
|------|-----------|
| Framework | FastAPI + SQLAlchemy 2.0 (Modern Type Mapping) |
| Seguridad | bcrypt (passwords) + itsdangerous (signed session cookies) |
| BD | SQLite (persistencia local con volúmenes Docker) |
| Despliegue | Docker (multi-stage) + EasyPanel + gosu (non-root) |

## Comandos

```powershell
# Desarrollo Local
.venv\Scripts\activate
.venv\Scripts\python.exe -m pytest -x
.venv\Scripts\python.exe -m ruff check src tests
.venv\Scripts\python.exe -m pytest --cov --cov-report=term-missing

# Docker (Versión Prueba)
docker-compose -f docker-compose.dev.yml up --build

# Inicialización (Seed)
$env:PYTHONPATH="src"; .venv\Scripts\python.exe -m app.seed
```

## Métricas actuales (post-SPRINT_19, 2026-09-04)

| Métrica | Valor |
|---------|-------|
| Tests | **78** (pytest -x ✅) |
| Linting | ruff clean ✅ · mypy clean ✅ |
| Cobertura | **88%** (657 líneas verificables; GUI excluida) |
| Última auditoría | AUDIT_12 — APROBADO (90.0% SDD) |
| Auditorías totales | 12 (todas APROBADAS) |

## Estado actual

- **Milestone v1 ✅**: Back-end completo, motor de reglas, seguridad y contenedorización.
- **Milestone v2 ✅**: Front-end (Streamlit) + Saneamiento de infraestructura y tipos.
- **Milestone v3 ✅**: Autogestión por Grupos, panel de coordinación, y lógica de vacaciones calendario.
- **Milestone v4 ✅**: Mejoras UX móvil, reglas avanzadas de permisos (anti-duplicidad, topes) y gestión de ciclo de vida de datos (cascada, contraseñas).
- **Milestone v5 ✅**: Mejoras de calendario (inicio domingo, tooltips, interactividad), UX móvil avanzada y seguridad (cambio de contraseña).
- **Milestone v6 ✅**: Despliegue VPS productivo (EasyPanel + migración BD), tooltip de grupos configurable, calendario interactivo con pre-carga de fecha.
- **Milestone v7 ✅**: Alineación modelo de concurrencia por grupo (calendario Opción A, RN4 composición), documentación sincronizada, operación VPS (logrotate + backup).
- **Milestone v8 ✅**: Alta de empleados desde el panel de Coordinación (cierra el CRUD de personal) y visibilidad de nombres de ausentes en el calendario para usuarios autenticados (RN5 reformulada en PLAN_09).
- **Milestone v9 ✅**: Deuda técnica de AUDIT_11 — módulo `roles.py`, `BaseAPIService` para los servicios GUI, `get_empleado_opcional()`, y medición de cobertura habilitada (88%).

### Historial de Sprints

| Sprint | Objetivo | Estado |
|--------|----------|--------|
| SPRINT_01 | Capa de festivos colombianos (`relevo.festivos`) | ✅ Done |
| SPRINT_02 | Base de datos y lógica de dominio | ✅ Done |
| SPRINT_03 | Autenticación y Seguridad (Auth Layer) | ✅ Done |
| SPRINT_04 | Endpoints de solicitudes (Business Flow) | ✅ Done |
| SPRINT_05 | Vista de disponibilidad anónima (RN5) | ✅ Done |
| SPRINT_06 | Contenedorización y Guía de Despliegue | ✅ Done |
| SPRINT_07 | GUI Autenticación (Streamlit login) | ✅ Done |
| SPRINT_08 | GUI Solicitudes (formulario + listado) | ✅ Done |
| SPRINT_09 | GUI Disponibilidad (calendario anónimo) | ✅ Done |
| SPRINT_10 | GUI Coordinación (panel de control) | ✅ Done |
| SPRINT_11 | Deuda técnica (tipos, linting, cobertura) | ✅ Done |
| SPRINT_12 | Autogestión de Grupos y Panel de Config | ✅ Done |
| SPRINT_13 | Mejoras UX móvil y reglas avanzadas | ✅ Done |
| SPRINT_14 | Mejoras de calendario y seguridad | ✅ Done |
| SPRINT_15 | Compatibilidad VPS (nombres de servicios) | ✅ Done |
| SPRINT_16 | Despliegue productivo VPS + calendario interactivo (C5+C6) | ✅ Done |
| SPRINT_17 | Alineación concurrencia por grupo, RN4, documentación (PLAN_08) | ✅ Done |
| SPRINT_18 | Alta de usuarios en GUI + nombres en calendario (PLAN_09) | ✅ Done |
| SPRINT_19 | Deuda técnica: roles, clase base GUI, cobertura (PLAN_10) | ✅ Done |
