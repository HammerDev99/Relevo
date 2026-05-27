# SPRINT_12 — Autogestión por Grupos (v3)

| Campo | Valor |
|-------|-------|
| **Fecha Inicio** | 2026-05-27 |
| **Fase CDAID** | Do |
| **Objetivo** | Implementar motor de grupos, lógica de vacaciones calendario y panel de configuración. |

## 1. Seguimiento de SPECs

| ID | Tarea | Estado | Verificación |
|----|-------|--------|--------------|
| **S13-C1** | Re-ingeniería del Motor de Grupos | `[x]` | tests/v1/test_grupos.py + Regresiones OK |
| **S13-C2** | Lógica de Vacaciones y Calendario | `[x]` | tests/v1/test_vacaciones_calendario.py |
| **S13-C3** | Sistema de Alertas y Autogestión | `[x]` | GUI adaptada + Default state='aprobada' |
| **S13-C4** | Panel de Configuración (Admin CRUD) | `[x]` | API Coordinacion + Tabs en GUI |

## 2. Métricas del Sprint

| Métrica | Inicial | Actual | Meta |
|---------|---------|--------|------|
| Tests Totales | 35 | 42 | > 40 |
| Cobertura | ~80% | ~85% | > 85% |
| Linter Errors | 0 | 0 | 0 |
| Mypy Errors | 0 | 0 | 0 |

## 3. Log de Actividad

- 2026-05-27: Inicio de Sprint 12.
- 2026-05-27: Implementado modelo `Grupo` y relación M:N con `Empleado` en `models.py`.
- 2026-05-27: Actualizada `validar_solicitud` en `domain.py` para usar concurrencia por grupo (S13-C1).
- 2026-05-27: Creado `tests/v1/test_grupos.py` para verificar lógica de grupos y multiafectación de Héctor.
- 2026-05-27: Finalizado SPEC-S13-C1.
- 2026-05-27: Modificado `domain.py` para usar días calendario en vacaciones y hábiles en permisos (S13-C2).
- 2026-05-27: Ajustado GUI en `01_solicitudes.py` proyectando 22 días calendario por defecto.
- 2026-05-27: Finalizado SPEC-S13-C2.
- 2026-05-27: Modificado el estado por defecto a `aprobada` en creación de solicitudes (Autogestión S13-C3).
- 2026-05-27: Añadido soporte para excepciones (+1 cupo) en reglas de dominio.
- 2026-05-27: Modificada GUI para filtrar respaldos por grupo y mostrar advertencia CUPO_LLENO con opción a excepción.
- 2026-05-27: Finalizado SPEC-S13-C3.
- 2026-05-27: Creados endpoints CRUD de usuarios y grupos en `routes/coordinacion.py` (S13-C4).
- 2026-05-27: Refactorizado `03_coordinacion.py` con 3 pestañas: Log de Auditoría, Gestión de Usuarios, y Grupos.
- 2026-05-27: Actualizado `seed.py` para poblar los 4 grupos y asignar a los 11 empleados.
- 2026-05-27: Sprint Completado. Todas las pruebas pasan sin errores de linter ni tipos.
- 2026-05-27: Fase Check completada. Se generó AUDIT_06 con veredicto APROBADO (100% conformidad SDD). Fixes de linting aplicados mediante TDD.

**Estado del Sprint: COMPLETADO y AUDITADO**

