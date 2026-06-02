# SPRINT_17 — Alineación del Modelo de Concurrencia y Documentación (PLAN_08)

| Campo | Valor |
|-------|-------|
| **Fecha** | 2026-06-02 |
| **Fase CDAID** | Do |
| **Milestone** | v7 |
| **SPECs** | SPEC-S16-A1, A2, B1..B6, S15-D5, D6 |
| **Estado** | ✅ Done |

---

## 1. Contexto

Sprint de corrección estructural: alinea el calendario de disponibilidad y toda la documentación con el modelo de concurrencia por grupo (autoritativo en `domain.py` desde v3/PLAN_05). Corrige además la validación de composición de excepciones (RN4) y documenta la operación del VPS (rotación de logs y backup).

---

## 2. Trabajo realizado

### 2.1 Fase A — Núcleo (TDD)

| SPEC | Cambios | Commits |
|------|---------|---------|
| SPEC-S16-A1 | `schemas/disponibilidad.py`: +`vista_general: bool`; `routes/disponibilidad.py`: cálculo por grupo (Opción A), `_empleado_de_sesion()`, `_estado_para_grupos()`; tests actualizados | `eaba50e` (RED), `68d4230` (GREEN) |
| SPEC-S16-A2 | `domain.py`: validación de composición excepción — vacaciones no permitidas como excepción, permiso requiere justificación (RN4); 3 tests nuevos | `490e94f` (RED), `2391c1c` (GREEN) |

### 2.2 Fase B — Documentación

| SPEC | Archivo | Cambio |
|------|---------|--------|
| B1 | `CLAUDE.md` | RN3/RN4 redefinidas por grupo; nota de migración modelo v1→v3 |
| B2 | `README.md` | Sección concurrencia por grupo; grupos incluyen cupo; calendario Opción A |
| B3 | `agent_docs/architecture.md` | Modelo concurrencia por grupo; tabla dominio vs calendario |
| B4 | `agent_docs/reglas_concurrencia.md` (nuevo) | Fórmula cupos, composición canónica grupos, ejemplos resueltos |
| B5 | `docs/others/comunicacion_empleados.md` (nuevo); PLAN_08 §8 corregido | Mensaje por grupo; corrección nota incorrecta |
| B6 | Reflejado en B4 | G3 = 3 miembros (JORGE, YESENIA, DANIELA → cupo 1) |

### 2.3 Fase C — Operación VPS

| SPEC | Cambio |
|------|--------|
| D5 | `deploy-vps-instructions.md` Fase 6: `logrotate` para logs de app + `daemon.json` para logs Docker |
| D6 | `deploy-vps-instructions.md` Fase 7: comandos de verificación crontab y primer backup manual |

---

## 3. Archivos creados/modificados

| Archivo | Tipo | SPEC |
|---------|------|------|
| `src/app/schemas/disponibilidad.py` | mod | A1 |
| `src/app/routes/disponibilidad.py` | mod | A1 |
| `src/app/domain.py` | mod | A2 |
| `tests/v1/test_disponibilidad.py` | mod | A1 |
| `tests/v1/test_domain.py` | mod | A2 |
| `CLAUDE.md` | mod | B1 |
| `README.md` | mod | B2 |
| `agent_docs/architecture.md` | mod | B3 |
| `agent_docs/reglas_concurrencia.md` | nuevo | B4, B6 |
| `docs/others/comunicacion_empleados.md` | nuevo | B5 |
| `docs/plannings/PLAN_08_*.md` | mod | B5, cierre |
| `docs/others/deploy-vps-instructions.md` | mod | D5, D6 |

---

## 4. Verificación final

| Herramienta | Resultado |
|-------------|-----------|
| `pytest -x` | ✅ 59 passed (baseline: 55) |
| `ruff check src tests` | ✅ All checks passed |
| Regresión | ✅ Sin regresiones |

### Tests nuevos

| Test | SPEC | Tipo |
|------|------|------|
| `test_disponibilidad_sin_pii` (actualizado) | A1 | Integration — vista general por grupos, RN5 |
| `test_disponibilidad_por_grupo_con_sesion` (nuevo) | A1 | Integration — estado personalizado por grupos del usuario |
| `test_excepcion_permiso_sin_justificacion_rechazada` (nuevo) | A2 | Unit — Failure path |
| `test_excepcion_vacaciones_rechazada` (nuevo) | A2 | Unit — Failure path |
| `test_excepcion_composicion_permiso_permiso_success` (nuevo) | A2 | Unit — Success path permiso+permiso |

---

## 5. Próximos pasos

- **Check**: Auditoría AUDIT_10 post-implementación PLAN_08 (tasa objetivo ≥ 85%).
- **Operación VPS manual**: Ejecutar rotación de logs y primer backup en el VPS (acciones M1 pendientes en §9 de PLAN_08).
- **Redeploy VPS** recomendado para activar los cambios de disponibilidad por grupo en producción.
