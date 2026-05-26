# SPRINT_03 — App Web v1 (Seguridad y Auth)

| Campo | Valor |
|-------|-------|
| **Fecha** | 2026-05-26 |
| **Fase CDAID** | Do |
| **Origen** | PLAN_02 |
| **Objetivo** | Implementar la capa de seguridad, autenticación de usuarios y gestión de sesiones. |

## SPECs entregados

| SPEC | Descripción | Estado | Criterios |
|------|-------------|--------|-----------|
| SPEC-V1-B3 | Auth: login, sesión, roles | ✅ Done | bcrypt; itsdangerous (firmado); dependencias FastAPI; 401/403 controlados |

## Artefactos

| Archivo | Rol |
|---------|-----|
| `src/app/auth.py` | Lógica de seguridad (hash, tokens, deps) |
| `src/app/routes/auth.py` | Endpoints de login/logout |
| `src/app/main.py` | Punto de entrada de la aplicación FastAPI |
| `tests/v1/test_auth.py` | Tests de integración de seguridad |

## Verificación (Check)

| Herramienta | Resultado |
|-------------|-----------|
| `pytest` | 31 passed (18 festivos + 8 dominio + 5 auth) |
| `ruff check` | All checks passed |

## Notas de Auditoría

- Se optó por `secure=False` en las cookies temporalmente para facilitar pruebas en desarrollo local sin HTTPS, pero se habilitará mediante configuración en producción.
- Las dependencias de FastAPI están listas para ser inyectadas en las rutas de solicitudes.

## Próximo paso

- **SPEC-V1-B4**: Endpoints solicitudes (creación y listado).
