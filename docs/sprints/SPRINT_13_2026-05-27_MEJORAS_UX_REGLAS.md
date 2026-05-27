# SPRINT_13 — Mejoras UX y Reglas de Negocio (v4)

| Campo | Valor |
|-------|-------|
| **Fecha Inicio** | 2026-05-27 |
| **Fase CDAID** | Do |
| **Objetivo** | Mejorar la experiencia de usuario, endurecer las reglas de dominio y habilitar gestión de datos en cascada. |

## 1. Seguimiento de SPECs

| ID | Tarea | Estado | Verificación |
|----|-------|--------|--------------|
| **S14-C1** | Gestión de Ciclo de Vida de Datos (Eliminación) | `[x]` | tests/v1/test_models.py, tests/v1/test_solicitudes.py, tests/v1/test_coordinacion.py |
| **S14-C2** | Reglas Avanzadas de Dominio (Control de Días) | `[x]` | tests/v1/test_domain.py |
| **S14-C3** | Automatización y Experiencia de Usuario (UI/UX) | `[x]` | GUI (01_solicitudes.py) verificada visualmente |
| **S14-C4** | Seguridad y Perfil de Usuario | `[ ]` | Pendiente (Endpoint /password y UI Perfil) |

## 2. Métricas del Sprint

| Métrica | Inicial | Actual | Meta |
|---------|---------|--------|------|
| Tests Totales | 42 | 47 | > 42 |
| Cobertura | ~85% | ~87% | > 85% |
| Linter Errors | 0 | 0 | 0 |
| Mypy Errors | 21 | 23 | 21 (Diferidos en v1 + 2 en tests) |

## 3. Log de Actividad

- 2026-05-27: Inicio de Sprint 13.
- 2026-05-27: SPEC-S14-C1 completado. Implementado borrado en cascada en SQLAlchemy, endpoints y botones en GUI. Test coverage verificado (+3 tests). Commit: `4479746`.
- 2026-05-27: SPEC-S14-C2 completado. Agregada validación de duplicidad de días y límite de 3 días por permiso en `domain.py`. Test coverage verificado (+2 tests). Commit: `e04e75b`.
- 2026-05-27: SPEC-S14-C3 completado. Implementada reactividad en fechas (mismo día para permisos, +22 días para vacaciones) y CSS responsivo para móviles. Commit: `a515995`.
- 2026-05-27: Cierre parcial del Sprint por solicitud del usuario. SPEC-S14-C4 queda pendiente para el próximo ciclo.

**Estado del Sprint: CERRADO PARCIALMENTE**

