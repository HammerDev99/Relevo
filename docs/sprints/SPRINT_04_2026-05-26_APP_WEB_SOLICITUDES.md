# SPRINT_04 — App Web v1 (Endpoints Solicitudes)

| Campo | Valor |
|-------|-------|
| **Fecha** | 2026-05-26 |
| **Fase CDAID** | Do |
| **Origen** | PLAN_02 |
| **Objetivo** | Implementar los endpoints para crear y listar solicitudes de ausencia con validación de dominio. |

## SPECs entregados

| SPEC | Descripción | Estado | Criterios |
|------|-------------|--------|-----------|
| SPEC-V1-B4 | Endpoints solicitudes | ✅ Done | POST `/solicitudes/nueva` (valida RNs); GET `/solicitudes` (filtrado por empleado) |

## Artefactos

| Archivo | Rol |
|---------|-----|
| `src/app/routes/solicitudes.py` | Endpoints de negocio |
| `src/app/main.py` | Registro de router y migración a lifespan |
| `tests/v1/test_solicitudes.py` | Tests de integración de solicitudes |

## Verificación (Check)

| Herramienta | Resultado |
|-------------|-----------|
| `pytest` | 34 passed (incluye validación de concurrencia vía API) |
| `ruff check` | Clean (excluyendo B008 inherente a FastAPI) |

## Notas de Auditoría

- Se migró el arranque de la app a `lifespan` para cumplir con las recomendaciones modernas de FastAPI.
- El endpoint de creación utiliza `Form` para compatibilidad futura con HTMX/Frontend clásico.
- Los errores de dominio se transforman correctamente en `400 Bad Request` con detalle para el usuario.

## Próximo paso

- **SPEC-V1-B5**: Vista de disponibilidad (calendario sin PII) + panel coordinación.
