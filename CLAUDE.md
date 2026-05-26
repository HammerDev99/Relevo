# Relevo — Sistema de gestión de ausencias (dependencia judicial, Colombia)

MVP para coordinar vacaciones y permisos de 10 empleados, con cupos de concurrencia y privacidad. Escalable a app web Python en VPS propio (dominio autorizado en la red de la Rama Judicial).

## Reglas críticas (6)

1. **Inmutabilidad**: todos los DTOs/modelos con `@dataclass(frozen=True)`. Nunca mutar; retornar copias.
2. **Errores**: usar `Result[T, E]` (`Success`/`Failure`), no `try/except` anidados ni excepciones para flujo de control.
3. **Logging**: `get_logger(__name__)`, nunca `logging.getLogger` directo.
4. **Privacidad (RN5)**: el dato sensible (nombre, motivo) jamás se expone públicamente. La capa pública solo ve estados derivados (`DISPONIBLE`/`OCUPADO`/`EXCEPCIONAL`).
5. **Dominio puro**: `src/relevo/` sin acoplamiento a Google/Trello → portable al VPS para la v1.
6. **Verificación**: todo cambio pasa `pytest -x` + `ruff check` + `mypy`. Tests cubren Success y Failure.

## Reglas de negocio (contrato)

| ID | Regla |
|----|-------|
| RN2 | 22 días vacaciones/año, 3 días permiso/mes por empleado |
| RN3 | Concurrencia estándar: máx **1** ausente a la vez |
| RN4 | Excepción: máx **2** (vacaciones+permiso, o 2 permisos justificados) |
| RN5 | Privacidad: empleados no ven quién/por qué |
| RN6 | Respaldo: acordar cobertura con un compañero antes de pedir permiso |
| RN7 | Festivos de Colombia (Ley Emiliani) + días hábiles reales |

## Navegación

| Necesito... | Ver |
|-------------|-----|
| Análisis del MVP, fallas, datos, paso a paso | `docs/plannings/PLAN_01_2026-05-26_MVP_AUSENCIAS.md` |
| Resumen de sprints | `docs/sprints/` |
| Auditorías de calidad | `docs/validate/` |
| Capa de cálculo (festivos, días hábiles) | `src/relevo/` |

## Comandos

```powershell
# Entorno
.venv\Scripts\activate
# Verificación
.venv\Scripts\python.exe -m pytest -x
.venv\Scripts\python.exe -m ruff check src tests
.venv\Scripts\python.exe -m mypy
```

## Estado actual

- **Sprint 01 ✅**: módulo de festivos colombianos (`src/relevo/`) — 18 tests, mypy strict.
- **Sprint 02+ 🔜**: app web v1 en VPS — ver `docs/plannings/PLAN_02_*.md`.

### Stack app web v1

| Capa | Tecnología |
|------|-----------|
| Framework | FastAPI + Jinja2 + HTMX |
| BD / ORM | SQLite + SQLAlchemy 2.x |
| Auth | Sesiones firmadas (`itsdangerous`) |
| Despliegue | Ubuntu + EasyPanel + Dockerfile |

### SPECs app web (pendientes)

| SPEC | Descripción |
|------|-------------|
| SPEC-V1-B1 | Modelos BD (Empleado, Solicitud) |
| SPEC-V1-B2 | Dominio: saldos (RN2) + concurrencia (RN3/RN4) |
| SPEC-V1-B3 | Auth: login, sesión, roles |
| SPEC-V1-B4 | Endpoints solicitudes |
| SPEC-V1-B5 | Vista de disponibilidad sin PII (RN5) |
| SPEC-V1-B6 | Dockerfile + despliegue EasyPanel |
