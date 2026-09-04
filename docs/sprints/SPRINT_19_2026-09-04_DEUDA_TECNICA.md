# SPRINT_19 — Deuda Técnica y Consistencia (PLAN_10)

| Campo | Valor |
|-------|-------|
| **Fecha** | 2026-09-04 |
| **Fase CDAID** | Do |
| **Milestone** | v9 |
| **SPECs** | SPEC-S19-A1, A2, B1, B2, B3, C1, C2, D1 (8 de 8) |
| **Estado** | ✅ Done |

---

## 1. Contexto

Sprint de deuda técnica **sin funcionalidad nueva**, salvo D1 (ajuste de alcance pedido durante el sprint). Salda las divergencias menores que AUDIT_11 identificó con las skills `/refactoring` y `/design-patterns`.

Regla aplicada: todo refactor debe pasar los tests existentes **sin modificarlos** — esa es la prueba de equivalencia.

---

## 2. Trabajo realizado

| SPEC | Cambios | Commit |
|------|---------|--------|
| **C1** | `pytest-cov` declarado e instalado; `[tool.coverage]` en `pyproject.toml` con la GUI excluida | `2d5365e` |
| **A1** | `UsuarioUpdate.rol` pasa a `RolUsuario \| None`; 2 tests nuevos (RED verificado) | `425d1e1` |
| **A2** | Nuevo `src/app/roles.py` con `ROL_EMPLEADO`, `ROL_COORDINACION` y el alias `RolUsuario`; consumido por 8 archivos | `425d1e1` |
| **B1** | `_resolver_grupos()` en `routes/coordinacion.py` | `08a3a8a` |
| **D1** | El desplegable táctil solo se renderiza con sesión activa | `08a3a8a` |
| **B3** | `get_empleado_opcional()` en `auth.py`; `_empleado_de_sesion()` eliminado | `3d004d6` |
| **B2** | `BaseAPIService`; los 4 servicios GUI migrados uno a uno | `08e4cab` |
| **C2** | LUISA, JOHN y BRIGITH retirados del seed; docs alineadas | (ver git log) |

### Hallazgos durante la ejecución

**`session_keys.USER_ID` nunca se escribe** (detectado en D1). `auth_service.login()` popula `IS_AUTHENTICATED`, `USER_EMAIL`, `USER_ROLE` y `AUTH_TOKEN`, pero no `USER_ID`.

Doble consecuencia:
1. Condicionar el panel a esa clave lo habría ocultado para **todos** los usuarios.
2. La caché de SPEC-S18-E1 venía recibiendo siempre `None` como clave de usuario, de modo que **no segmentaba por sesión**: dos usuarios podían compartir respuesta cacheada, con riesgo para RN5. Corregido usando `USER_EMAIL`.

**Cobertura real medida por primera vez** (C1). La regla del 80% se venía afirmando sin verificarla porque `pytest-cov` no estaba instalado. Resultado: **86%** sobre código verificable (88% al cierre del sprint). Sin excluir la GUI el número es 40%, cifra que no refleja la verificación del backend — de ahí el `omit` documentado.

**Sin timeout HTTP** (detectado en B2). Ninguna petición de la GUI tenía timeout: una respuesta colgada bloqueaba la interfaz indefinidamente. `BaseAPIService` fija 10s.

---

## 3. Métricas post-fase

| Métrica | Pre-sprint | Post-sprint |
|---------|:----------:|:-----------:|
| Tests | 76 | **78** |
| Ruff | limpio | limpio |
| Mypy | limpio (43) | limpio (45) |
| Cobertura | no medible | **88%** |
| Bloques `httpx.Client` en servicios | 19 | **1** |
| Líneas de los 4 servicios concretos | 425 | **308** (−28%) |
| Literales de rol fuera de `roles.py` | 12 | **0** |

---

## 4. Archivos creados/modificados

| Archivo | Tipo | SPEC |
|---------|------|------|
| `src/app/roles.py` | Nuevo | A1, A2 |
| `src/app/gui/services/base_service.py` | Nuevo | B2 |
| `src/app/schemas/usuarios.py` | Mod | A1, A2 |
| `src/app/auth.py` | Mod | A2, B3 |
| `src/app/models.py`, `src/app/seed.py` | Mod | A2 |
| `src/app/routes/coordinacion.py` | Mod | B1 |
| `src/app/routes/disponibilidad.py` | Mod | B3 |
| `src/app/gui/services/*.py` (4) | Mod | B2 |
| `src/app/gui/pages/01_solicitudes.py` | Mod | B2 |
| `src/app/gui/pages/02_disponibilidad.py` | Mod | D1 |
| `src/app/gui/pages/03_coordinacion.py`, `portal.py` | Mod | A2 |
| `tests/v1/test_coordinacion.py` | Mod | A1 |
| `pyproject.toml` | Mod | C1 |

---

## 5. Pendiente al cierre

- [x] **SPEC-S19-C2** resuelto: el usuario decidió retirar del seed a LUISA, JOHN y BRIGITH (2026-09-04).
- [ ] Desplegar al VPS (push dispara ambos webhooks).
- [x] **AUDIT_12** — ✅ APROBADO (90.0% SDD, 2 defectos corregidos en fase Act). Ver `docs/validate/AUDIT_12_2026-09-04_GATE_V9_DEUDA_TECNICA.md`.
- [ ] Backlog → PLAN_11: `routes/coordinacion.py` al 57% de cobertura (subió desde 46% por los tests de A1); `session_keys.USER_ID` declarado pero nunca escrito.

---

## 6. Listo para Check

El milestone está listo para auditoría: gate de transición superado (78 tests, ruff y mypy limpios, cobertura 88%), los 8 SPECs completados.
