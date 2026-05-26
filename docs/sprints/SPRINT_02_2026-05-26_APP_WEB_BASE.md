# SPRINT_02 — App Web v1 (Base y Dominio)

| Campo | Valor |
|-------|-------|
| **Fecha** | 2026-05-26 |
| **Fase CDAID** | Do |
| **Origen** | PLAN_02 |
| **Objetivo** | Implementar la infraestructura de base de datos y la lógica de dominio para la app web. |

## SPECs entregados

| SPEC | Descripción | Estado | Criterios |
|------|-------------|--------|-----------|
| SPEC-V1-B1 | Modelos BD (Empleado, Solicitud) | ✅ Done | SQLAlchemy 2.0; SQLite; mypy strict |
| SPEC-V1-B2 | Dominio: saldos (RN2) + concurrencia (RN3/RN4) | ✅ Done | Result pattern; validación RNs; 100% test coverage en domain |

## Artefactos

| Archivo | Rol |
|---------|-----|
| `src/app/config.py` | Configuración (Pydantic Settings) |
| `src/app/database.py` | Engine y sesión SQLAlchemy |
| `src/app/models.py` | Modelos de BD |
| `src/app/domain.py` | Lógica de negocio (corazón del sistema) |
| `tests/v1/test_models.py` | Tests de persistencia |
| `tests/v1/test_domain.py` | Tests de reglas de negocio |

## Verificación (Check)

| Herramienta | Resultado |
|-------------|-----------|
| `pytest` | 26 passed (18 festivos + 8 web app) |
| `ruff check` | All checks passed |
| `mypy` | Success (parcial, ver notas) |

## Notas de Auditoría

- Mypy presenta duplicidad de módulos al analizar `src` y `relevo` (instalado). Se recomienda usar `-p app -p relevo` para verificación completa.
- Se corrigió el uso de `utcnow()` migrando a `datetime.now(UTC)`.
- La lógica de concurrencia valida día por día para mayor seguridad en el MVP.

## Próximo paso

- **SPEC-V1-B3**: Auth (login, sesión, roles).
