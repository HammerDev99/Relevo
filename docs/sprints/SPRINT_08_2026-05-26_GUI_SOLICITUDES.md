# SPRINT_08 — Portal del Empleado (Mis Solicitudes)

| Campo | Valor |
|-------|-------|
| **Fecha** | 2026-05-26 |
| **Fase CDAID** | Do |
| **Origen** | PLAN_03 |
| **Objetivo** | Implementar la interfaz de gestión de solicitudes para empleados, integrada con el backend. |

## SPECs entregados

| SPEC | Descripción | Estado | Criterios |
|------|-------------|--------|-----------|
| SPEC-V2-F2 | Portal del Empleado | ✅ Done | Listado de solicitudes; Formulario reactivo; Validación de RNs en UI |

## Artefactos

| Archivo | Rol |
|---------|-----|
| `src/app/gui/pages/01_solicitudes.py` | Página principal de solicitudes |
| `src/app/gui/services/solicitud_service.py` | Cliente HTTP para solicitudes |
| `src/app/routes/auth.py` | Añadido endpoint `/usuarios` para el selector |

## Verificación (Check)

| Herramienta | Resultado |
|-------------|-----------|
| `pytest` | 35 passed (Backend) |
| `Funcional` | Flujo de creación verificado en Docker (API + GUI) |

## Notas de Auditoría

- Se integró el selector de compañeros de respaldo filtrando al usuario actual.
- Los errores de dominio (cupo lleno) se muestran como alertas rojas en el formulario.

## Próximo paso

- **SPEC-V2-F3**: Calendario de Disponibilidad anónimo.
