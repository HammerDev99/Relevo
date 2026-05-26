# SPRINT_05 — App Web v1 (Disponibilidad y RN5)

| Campo | Valor |
|-------|-------|
| **Fecha** | 2026-05-26 |
| **Fase CDAID** | Do |
| **Origen** | PLAN_02 |
| **Objetivo** | Implementar la vista de disponibilidad pública cumpliendo con la restricción de privacidad RN5. |

## SPECs entregados

| SPEC | Descripción | Estado | Criterios |
|------|-------------|--------|-----------|
| SPEC-V1-B5 | Vista de disponibilidad (RN5) | ✅ Done | `/disponibilidad` sin PII; estados DISPONIBLE/OCUPADO/EXCEPCIONAL |

## Artefactos

| Archivo | Rol |
|---------|-----|
| `src/app/routes/disponibilidad.py` | Lógica de consulta de calendario anónimo |
| `tests/v1/test_disponibilidad.py` | Verificación de privacidad y estados |

## Verificación (Check)

| Herramienta | Resultado |
|-------------|-----------|
| `pytest` | 35 passed |
| `ruff check` | Clean (excluyendo B008 FastAPI) |

## Notas de Auditoría

- Se garantiza la RN5 al no serializar el objeto `Solicitud` completo, sino solo la fecha y el estado calculado.
- La vista de disponibilidad es accesible para cualquier usuario autenticado (o incluso pública si se deseara, pero por ahora está en el router de la app).

## Próximo paso

- **SPEC-V1-B6**: Dockerfile + despliegue EasyPanel (Cierre v1).
