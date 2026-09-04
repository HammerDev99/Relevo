# SPRINT_18 — Alta de Usuarios en GUI y Visibilidad de Ausencias (PLAN_09)

| Campo | Valor |
|-------|-------|
| **Fecha** | 2026-09-04 |
| **Fase CDAID** | Do |
| **Milestone** | v8 |
| **SPECs** | SPEC-S18-B1..B5, A1..A4, C1, D1..D2 (12) |
| **Estado** | ✅ Done |

---

## 1. Contexto

Sprint de dos frentes independientes:

1. **Fase B (P0)** — Cierra la brecha del CRUD de personal. Existían `GET`, `PATCH` y `DELETE` de usuarios, pero no `POST`, lo que obligó a dar de alta tres empleados por consola contra la BD del VPS el 2026-09-04.
2. **Fase A (P1)** — Reformula RN5 para que el calendario muestre los nombres de los ausentes a usuarios autenticados.

Orden de ejecución: Fase B primero, por no tener decisiones pendientes.

---

## 2. Trabajo realizado

### 2.1 Fase B — Alta de usuarios (TDD)

| SPEC | Cambios | Commit |
|------|---------|--------|
| SPEC-S18-B1 | `schemas/usuarios.py`: `UsuarioCreate` frozen, `password` con `min_length=8`, `rol` como `Literal["empleado","coordinacion"]`, constante `LONGITUD_MINIMA_PASSWORD` | `5225e96` |
| SPEC-S18-B2 | `routes/coordinacion.py`: `POST /coordinacion/usuarios` con `get_coordinador`, hash bcrypt, 400 en correo duplicado, asignación M:N de grupos | `5225e96` |
| SPEC-S18-B3 | `gui/services/coordinacion_service.py`: `crear_usuario()` con `@log_gui_action`, propagación de `detail` y mensaje específico para 422 | `5225e96` |
| SPEC-S18-B4 | `gui/pages/03_coordinacion.py`: expander "Registrar Nuevo Empleado" en `tab_users`, reutilizando `opciones_grupos` | `5225e96` |
| SPEC-S18-B5 | `tests/v1/test_coordinacion.py`: 6 tests (2 Success, 4 Failure) | `5225e96` |

**Reutilización**: el endpoint replica el patrón de `crear_grupo` y la asignación de grupos de `actualizar_usuario`. El formulario replica el de "Crear Nuevo Grupo" de la pestaña Grupos. No se introdujo arquitectura nueva.

### 2.2 Fase A — Nombres en el calendario (TDD)

| SPEC | Cambios | Commit |
|------|---------|--------|
| SPEC-S18-A1 | `schemas/disponibilidad.py`: +`empleados_ausentes: list[str]`; `routes/disponibilidad.py`: poblado solo si hay sesión válida, reutilizando el `selectinload` existente | (ver §5) |
| SPEC-S18-A2 | `gui/pages/02_disponibilidad.py`: tooltip compuesto "Ausentes: … \| Grupos con ausencias: …", con `html.escape()` sobre el atributo `title` | (ver §5) |
| SPEC-S18-A3 | `CLAUDE.md`, `README.md`, `agent_docs/reglas_concurrencia.md` §6 | (ver §5) |
| SPEC-S18-A4 | `tests/v1/test_disponibilidad.py`: test de PII reformulado + 2 tests nuevos | (ver §5) |

**Decisión de contrato**: RN5 se **reformula, no se deroga**. Se exponen solo nombres, solo a usuarios autenticados. Tipo y justificación permanecen protegidos en todos los casos. Ver PLAN_09 §3.

### 2.3 Fase C — Idempotencia del seed (TDD)

| SPEC | Cambios | Commit |
|------|---------|--------|
| SPEC-S18-C1 | `seed.py`: la asignación de grupos pasa dentro del `if not user`; se elimina la reescritura de `min_presentes`. `tests/v1/test_seed.py` nuevo con 4 tests | `fbc5cd8` |

Detectado al preparar el despliegue: el seed corre en cada arranque y revertía los grupos ajustados desde Coordinación. **Confirmado con datos reales**: el snapshot previo al despliegue mostraba a YESENIA, FLOR y DANIEL en G2/G2/G3 frente a G3/G1/G2 del seed. Tras el despliegue conservaron sus grupos — el fix quedó demostrado en producción.

### 2.4 Fase D — Correcciones post-despliegue (TDD)

| SPEC | Cambios | Commit |
|------|---------|--------|
| SPEC-S18-D1 | `routes/disponibilidad.py`: el estado evalúa siempre todos los grupos; `+estado_grupo_propio` reutilizando `_estado_para_grupos()`. Tooltip con aviso `Tu grupo: …`. 3 tests nuevos + 1 actualizado | (ver git log) |
| SPEC-S18-D2 | `gui/pages/04_perfil.py`: el cambio de contraseña pasa a `st.form` + `st.form_submit_button` | (ver git log) |

**Causa raíz de D2** (corrige el diagnóstico preliminar de "doble click"): `st.button` fuera de `st.form` con `text_input` que tienen `key=` hace que Streamlit reejecute el bloque y emita un segundo `PATCH` con la contraseña ya obsoleta. Determinista, sin intervención del usuario.

---

## 3. Archivos creados/modificados

| Archivo | Tipo | SPEC |
|---------|------|------|
| `docs/plannings/PLAN_09_*.md` | Nuevo | — |
| `docs/sprints/SPRINT_18_*.md` | Nuevo | — |
| `src/app/schemas/usuarios.py` | Modificado | B1 |
| `src/app/routes/coordinacion.py` | Modificado | B2 |
| `src/app/gui/services/coordinacion_service.py` | Modificado | B3 |
| `src/app/gui/pages/03_coordinacion.py` | Modificado | B4 |
| `tests/v1/test_coordinacion.py` | Modificado | B5 |
| `src/app/schemas/disponibilidad.py` | Modificado | A1 |
| `src/app/routes/disponibilidad.py` | Modificado | A1 |
| `src/app/gui/pages/02_disponibilidad.py` | Modificado | A2, D1 |
| `src/app/seed.py`, `tests/v1/test_seed.py` | Mod / Nuevo | C1 |
| `src/app/gui/pages/04_perfil.py` | Modificado | D2 |
| `docs/others/actualizacion-vps.md` | Nuevo | — (operación) |
| `CLAUDE.md`, `README.md`, `agent_docs/reglas_concurrencia.md` | Modificado | A3 |
| `tests/v1/test_disponibilidad.py` | Modificado | A4 |
| `scripts/crear_empleados.py` | Nuevo | — (contingencia) |

---

## 4. Verificación

| Check | Resultado |
|-------|-----------|
| `pytest` | **75 passed** (60 previos + 15 nuevos), sin regresión |
| `ruff check src tests scripts` | Limpio |
| Tests Success/Failure | 6 en Fase B (2/4), 2 nuevos + 1 reformulado en Fase A |

**Cobertura de invariantes de privacidad**: tres tests bloquean regresiones sobre RN5 — sin sesión no hay nombres, con sesión sí los hay, y la justificación nunca aparece.

---

## 5. Pendiente al cierre del sprint

- [ ] AUDIT_11 (fase Check) — auditoría del milestone v8.
- [x] Despliegue al VPS (2026-09-04) — digest verificado, `GIT_SHA=93098773d1`, datos intactos.
- [ ] **Rotación de la contraseña de coordinación (`admin123`)** — deuda P0 vencida desde v6, heredada a PLAN_09 §5.
