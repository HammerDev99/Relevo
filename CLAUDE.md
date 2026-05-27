# Relevo — Sistema de gestión de ausencias (dependencia judicial, Colombia)

MVP para coordinar vacaciones y permisos de 10 empleados, con cupos de concurrencia y privacidad. App web Python desplegada en VPS propio (dominio autorizado en la red de la Rama Judicial).

## Reglas críticas (6)

1. **Inmutabilidad**: modelos de dominio y DTOs preferiblemente inmutables. Modelos de persistencia (SQLAlchemy 2.0) con tipado estricto `Mapped`.
2. **Errores**: usar `Result[T, E]` (`Success`/`Failure`), no `try/except` anidados ni excepciones para flujo de control en lógica de negocio.
3. **Logging**: `get_logger(__name__)`, nunca `logging.getLogger` directo.
4. **Privacidad (RN5)**: el dato sensible (nombre, motivo) jamás se expone públicamente. La capa pública (`/disponibilidad`) solo ve estados derivados (`DISPONIBLE`/`OCUPADO`/`EXCEPCIONAL`).
5. **Arquitectura**: Separación clara entre `src/relevo` (festivos), `src/app/models` (persistencia), `src/app/domain` (reglas de negocio) y `src/app/routes` (FastAPI).
6. **Verificación**: todo cambio pasa `pytest -x` + `ruff check`. Tests cubren Success y Failure.

## Reglas de negocio (contrato)

| ID | Regla |
|----|-------|
| RN2 | 22 días vacaciones/año, 3 días permiso/mes por empleado |
| RN3 | Concurrencia estándar: máx **1** ausente a la vez |
| RN4 | Excepción: máx **2** (vacaciones+permiso, o 2 permisos justificados) |
| RN5 | Privacidad: empleados no ven quién/por qué |
| RN6 | Respaldo: acordar cobertura con un compañero antes de pedir permiso |
| RN7 | Festivos de Colombia (Ley Emiliani) + días hábiles reales |

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

# Docker (Versión Prueba)
docker-compose -f docker-compose.dev.yml up --build

# Inicialización (Seed)
$env:PYTHONPATH="src"; .venv\Scripts\python.exe -m app.seed
```

## Estado actual

- **Milestone v1 ✅**: Back-end completo, motor de reglas, seguridad y contenedorización.
- **Milestone v2 ✅**: Front-end (Streamlit) + Saneamiento de infraestructura y tipos.
- **Milestone v3 ✅**: Autogestión por Grupos, panel de coordinación, y lógica de vacaciones calendario.

### Historial de Sprints

| Sprint | Objetivo | Estado |
|--------|----------|--------|
| SPRINT_01 | Capa de festivos colombianos (`relevo.festivos`) | ✅ Done |
| SPRINT_02 | Base de datos y lógica de dominio | ✅ Done |
| SPRINT_03 | Autenticación y Seguridad (Auth Layer) | ✅ Done |
| SPRINT_04 | Endpoints de solicitudes (Business Flow) | ✅ Done |
| SPRINT_05 | Vista de disponibilidad anónima (RN5) | ✅ Done |
| SPRINT_06 | Contenedorización y Guía de Despliegue | ✅ Done |
| SPRINT_12 | Autogestión de Grupos y Panel de Config | ✅ Done |
