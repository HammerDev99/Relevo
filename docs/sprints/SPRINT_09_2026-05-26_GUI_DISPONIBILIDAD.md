# SPRINT_09 — Calendario de Disponibilidad (RN5)

| Campo | Valor |
|-------|-------|
| **Fecha** | 2026-05-26 |
| **Fase CDAID** | Do |
| **Origen** | PLAN_03 |
| **Objetivo** | Visualización gráfica del calendario de ausencias sin exponer datos personales. |

## SPECs entregados

| SPEC | Descripción | Estado | Criterios |
|------|-------------|--------|-----------|
| SPEC-V2-F3 | Calendario Disponibilidad | ✅ Done | Grid mensual; Semáforo de estados; Cumplimiento RN5 |

## Artefactos

| Archivo | Rol |
|---------|-----|
| `src/app/gui/pages/02_disponibilidad.py` | UI del calendario (Grid HTML/CSS) |
| `src/app/gui/services/disponibilidad_service.py` | Cliente HTTP para disponibilidad anónima |

## Verificación (Check)

| Herramienta | Resultado |
|-------------|-----------|
| `Funcional` | Verificado visualmente: Disponible (Verde), Ocupado (Amarillo), Lleno (Rojo) |
| `Privacidad` | Inspección de red confirma que no viajan nombres ni IDs de empleados |

## Notas de Auditoría

- Se utilizó un componente de grid personalizado inyectando HTML en Streamlit para mayor control visual.

## Próximo paso

- **SPEC-V2-F4**: Panel de Coordinación (Admin).
