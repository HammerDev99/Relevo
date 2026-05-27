# SPRINT_07 — Infraestructura y Auth GUI

| Campo | Valor |
|-------|-------|
| **Fecha** | 2026-05-26 |
| **Fase CDAID** | Do |
| **Origen** | PLAN_03 |
| **Objetivo** | Implementar la infraestructura base de Streamlit y el servicio de autenticación cliente. |

## SPECs entregados

| SPEC | Descripción | Estado | Criterios |
|------|-------------|--------|-----------|
| SPEC-V2-F1 | Infraestructura y Auth GUI | ✅ Done | Estructura modular; AuthService funcional; Login integrado con API |

## Artefactos

| Archivo | Rol |
|---------|-----|
| `src/app/gui/app.py` | Entrada Streamlit y shell de UI |
| `src/app/gui/session_keys.py` | Gestión de estado centralizada |
| `src/app/gui/services/auth_service.py` | Cliente HTTP para la API de Auth |
| `docker-compose.dev.yml` | Orquestación Dual (API + GUI) |

## Verificación (Check)

| Herramienta | Resultado |
|-------------|-----------|
| `pytest` | N/A para GUI por ahora (validación manual en Docker) |
| `ruff check` | Clean (excluyendo B008 FastAPI) |
| `Funcional` | Login verificado visualmente en Docker |

## Notas de Auditoría

- Se adoptó el patrón de **Sherlock Docs** para el manejo de sesiones y estructura de carpetas.
- La comunicación se realiza 100% vía HTTP REST hacia el servicio `api`.
- Se implementó el switch `RELEVO_MODE=gui|api` en el entrypoint.

## Próximo paso

- **SPEC-V2-F2**: Portal del Empleado (Mis Solicitudes y Formulario).
