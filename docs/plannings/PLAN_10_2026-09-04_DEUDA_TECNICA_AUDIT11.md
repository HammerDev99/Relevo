# PLAN_10 — Milestone v9 "Deuda Técnica y Consistencia (backlog AUDIT_11)"

| Campo | Valor |
|-------|-------|
| **Fecha** | 2026-09-04 |
| **Fase CDAID** | Plan |
| **Milestone** | v9 |
| **Origen** | Hallazgos diferidos de AUDIT_11 §5 + discrepancias detectadas durante SPRINT_18 |
| **Objetivo** | Saldar la deuda técnica que AUDIT_11 identificó con las skills `/refactoring` y `/design-patterns`, sin añadir funcionalidad nueva. Elevar la tasa SDD neta por encima del 85% eliminando las divergencias menores heredadas. |

---

## 1. Estado Previo / Contexto

AUDIT_11 (2026-09-04) fue la primera auditoría del proyecto que usó skills especializadas como instrumentos de verificación. Resultado: **APROBADO**, con 22 hallazgos — 12 CONFORME, 2 JUSTIFICADA, 6 MENOR, 2 DEFECTO.

Los 2 DEFECTOS se corrigieron en la fase Act del propio sprint. Las **6 divergencias menores** quedaron diferidas: son deuda de diseño sin impacto funcional inmediato, pero acumulan riesgo.

| Métrica | Estado actual |
|---------|---------------|
| Tests | 76 passed |
| Ruff | limpio |
| Mypy | limpio (43 archivos) |
| Tasa SDD AUDIT_11 | 63.6% bruta / 84.2% neta |

**Meta de este milestone**: cerrar 4 de las 6 divergencias menores y habilitar la medición de cobertura, que hoy no es posible.

> **Restricción de alcance**: este planning **no añade funcionalidad**. Todo cambio debe ser refactor con tests que demuestren comportamiento equivalente (regla: nunca mezclar refactor con feature en el mismo commit).

---

## 2. SPECs de Implementación (Milestone v9)

### Fase A — Seguridad y consistencia de contratos (P1)

#### SPEC-S19-A1: Whitelist de rol en `UsuarioUpdate`
- **Origen**: AUDIT_11 H8
- **Descripción**: `UsuarioCreate.rol` usa `Literal["empleado","coordinacion"]`, pero `UsuarioUpdate.rol` es `str | None` sin restricción. Un `PATCH` admite roles arbitrarios (`"superadmin"`, `""`), que quedarían persistidos y romperían `get_coordinador`, cuya comparación es `!= "coordinacion"`.
- **Riesgo actual**: bajo — solo explotable por una cuenta de coordinación ya autenticada. Pero un error de tipeo desde la GUI dejaría al usuario sin rol válido y sin acceso.
- **Archivos**: `src/app/schemas/usuarios.py`
- **Criterios de Aceptación**:
    - [x] `UsuarioUpdate.rol` pasa a `Literal["empleado","coordinacion"] | None`.
    - [x] Extraer el tipo a un alias compartido (`RolUsuario`) usado por `UsuarioCreate` y `UsuarioUpdate` — *Replace Magic Number with Symbolic Constant* aplicado a strings de rol.
    - [x] Test Failure: `PATCH` con rol inválido → 422.
    - [x] Test Success: `PATCH` con rol válido sigue funcionando (sin regresión).
- **Prioridad**: P1
- **Estado**: `[x]` | **Verificado**: 2026-09-04

#### SPEC-S19-A2: Unificar el rol en una constante de dominio
- **Descripción**: el literal `"coordinacion"` aparece disperso (`auth.py::get_coordinador`, `seed.py`, schemas, GUI). Un cambio de nomenclatura exigiría *Shotgun Surgery*.
- **Archivos**: `src/app/roles.py` (nuevo), `auth.py`, `models.py`, `seed.py`, `schemas/usuarios.py`, `gui/portal.py`, `gui/pages/03_coordinacion.py`, `gui/services/auth_service.py`
- **Criterios de Aceptación**:
    - [x] Constantes `ROL_EMPLEADO` / `ROL_COORDINACION` en un único módulo.
    - [x] `auth.py`, `seed.py` y schemas las consumen; sin literales sueltos en lógica de autorización.
    - [x] Sin cambio de comportamiento: los tests existentes pasan sin modificarse.
- **Prioridad**: P2
- **Estado**: `[x]` | **Verificado**: 2026-09-04

### Fase B — Eliminación de duplicación (P2)

#### SPEC-S19-B1: `_resolver_grupos()` en el router de coordinación
- **Origen**: AUDIT_11 H9
- **Descripción**: `db.scalars(select(Grupo).where(Grupo.id.in_(...)))` se repite en `crear_usuario` (`:90`) y `actualizar_usuario` (`:117`). Técnica: *Extract Method*.
- **Nota**: son 2 ocurrencias — la Regla de Tres aún no obliga. Se incluye porque el alta de usuarios (SPEC-S18-B2) ya la elevó a 2 y una tercera es previsible.
- **Archivos**: `src/app/routes/coordinacion.py`
- **Criterios de Aceptación**:
    - [x] Helper `_resolver_grupos(db, grupo_ids) -> list[Grupo]`.
    - [x] Ambos endpoints lo consumen; comportamiento idéntico.
    - [x] Los tests de `test_coordinacion.py` pasan sin modificarse (prueba de equivalencia).
- **Prioridad**: P2
- **Estado**: `[x]` | **Verificado**: 2026-09-04

#### SPEC-S19-B2: Clase base para los servicios GUI
- **Origen**: AUDIT_11 H14
- **Descripción**: los 4 servicios GUI repiten el mismo bloque `try / httpx.Client(base_url) / status_code == 200 / except → st.error` **19 veces**. Es **Duplicate Code** estructural. Técnica: *Extract Superclass* (`BaseAPIService`) con métodos `_get`, `_post`, `_patch`, `_delete` que centralicen transporte, cabeceras de sesión y manejo de error.
- **Beneficio adicional**: hoy cada método decide por su cuenta si muestra `st.error` o devuelve `False` en silencio — comportamiento inconsistente ante fallos de red.
- **Archivos**: `src/app/gui/services/base_service.py` (nuevo), los 4 servicios existentes
- **Criterios de Aceptación**:
    - [ ] `BaseAPIService` con `base_url`, `get_auth_headers()` y helpers HTTP.
    - [ ] Los 4 servicios heredan; el bloque `httpx.Client` desaparece de los métodos individuales.
    - [ ] Manejo de error homogéneo y documentado.
    - [ ] Sin cambios en la firma pública de los métodos: las páginas no se tocan.
- **Prioridad**: P2 — el de mayor impacto en líneas, y el de mayor riesgo de regresión
- **Estado**: `[ ]`

#### SPEC-S19-B3: `get_empleado_opcional()` en `auth.py`
- **Origen**: AUDIT_11 H20 (heredado de AUDIT_10 H16 — **dos auditorías diferido**)
- **Descripción**: `disponibilidad.py::_empleado_de_sesion()` duplica la lógica de `auth.py::get_empleado_actual()`, con la única diferencia de devolver `None` en vez de lanzar `HTTPException`. Viola **DIP**: el router implementa autenticación en vez de depender de la capa de auth.
- **Archivos**: `src/app/auth.py`, `src/app/routes/disponibilidad.py`
- **Criterios de Aceptación**:
    - [ ] `get_empleado_opcional(request, db) -> Empleado | None` en `auth.py`.
    - [ ] `get_empleado_actual()` se reescribe sobre ella (lanza si es `None`), eliminando la duplicación en ambos sentidos.
    - [ ] `_empleado_de_sesion()` se elimina de `disponibilidad.py`.
    - [ ] Los tests de disponibilidad y auth pasan sin modificarse.
- **Prioridad**: P2
- **Estado**: `[ ]`

### Fase C — Capacidad de verificación (P1)

#### SPEC-S19-C1: Habilitar medición de cobertura
- **Origen**: detectado al preparar PLAN_10 — `pytest --cov` falla con *unrecognized arguments*.
- **Descripción**: `pytest-cov` no está instalado ni declarado. La regla de **80% de cobertura mínima** (`~/.claude/rules/common/testing.md` y convenciones del proyecto) **no es verificable hoy**: se ha venido afirmando sin medirla.
- **Archivos**: `pyproject.toml`, `requirements.txt`
- **Criterios de Aceptación**:
    - [x] `pytest-cov` en dependencias de desarrollo.
    - [x] `pytest --cov=src --cov-report=term-missing` ejecutable.
    - [x] Cobertura real medida y registrada como línea base en `CLAUDE.md`: **86%** sobre 655 líneas verificables.
    - [x] Brecha documentada: **86% ≥ 80%**, la regla se cumple. Medición global sin excluir GUI: 40% (1402 líneas) — la capa Streamlit no es testeable sin `AppTest` (AUDIT_11 H22), por lo que `[tool.coverage.run] omit` la excluye para que la métrica refleje la verificación real.
    - [x] Punto débil identificado: `routes/coordinacion.py` al **46%** — los endpoints de solicitudes y grupos carecen de tests. Se registra como hallazgo para el siguiente Planning, fuera del alcance de este milestone (que es refactor, no tests nuevos).
- **Prioridad**: **P1** — condiciona la validez de las métricas de todas las auditorías previas
- **Estado**: `[x]` | **Verificado**: 2026-09-04

#### SPEC-S19-C2: Corregir la discrepancia de BRIGITH
- **Origen**: detectada el 2026-09-04, diferida en PLAN_09 §5
- **Descripción**: `seed.py:61` tiene a BRIGITH **sin grupo** (decisión 2026-06-02), pero `CREDENCIALES_PRUEBA.md:27` la lista en *G3: Reparto Const. y Penal*. Una de las dos fuentes miente.
- **Impacto**: sin grupo, BRIGITH no consume cupo de RN3 y sus solicitudes se aprueban sin restricción de concurrencia. Si el dato correcto es G3, el motor la está tratando mal.
- **Criterios de Aceptación**:
    - [ ] **Confirmar con el usuario** cuál es la composición real antes de tocar nada.
    - [ ] Alinear `seed.py`, `CREDENCIALES_PRUEBA.md` y `agent_docs/reglas_concurrencia.md` §2.
    - [ ] Verificar el estado en la BD de producción (el seed ya no reasigna grupos: SPEC-S18-C1).
- **Prioridad**: P1 — afecta la aplicación de RN3
- **Estado**: `[ ]` — **bloqueado**: requiere decisión del usuario

### Fase D — Ajuste de alcance del listado táctil (P1)

#### SPEC-S19-D1: El listado de ausencias solo para usuarios autenticados
- **Origen**: solicitud del usuario (2026-09-04), tras el despliegue de SPEC-S18-E2.
- **Descripción**: el desplegable *"📋 Detalle de días con ausencias (N)"* se renderiza siempre que haya días con ausencias, **también sin sesión iniciada**. En esa vista `empleados_ausentes` viene vacío por RN5, de modo que el panel solo muestra nombres de grupo: información redundante con el color del calendario y con el tooltip.
- **Decisión**: mostrar el desplegable **únicamente con sesión activa**. El calendario, los colores, la leyenda y el tooltip permanecen **sin cambios** en ambas vistas.
- **Coherencia con RN5**: refuerza la separación ya establecida — la vista anónima no ofrece un panel de detalle; los nombres siguen siendo exclusivos de usuarios autenticados.
- **Archivos**: `src/app/gui/pages/02_disponibilidad.py`
- **Criterios de Aceptación**:
    - [x] El desplegable solo se renderiza si hay sesión iniciada.
    - [x] Sin sesión: el calendario funciona igual (colores, leyenda, navegación, tooltip de grupos).
    - [x] Con sesión: comportamiento idéntico al actual.
    - [x] Se reutiliza el indicador de sesión ya disponible, sin peticiones nuevas.

> **Hallazgo durante la implementación**: `session_keys.USER_ID` **nunca se
> escribe** — `auth_service.login()` popula `IS_AUTHENTICATED`, `USER_EMAIL`,
> `USER_ROLE` y `AUTH_TOKEN`, pero no `USER_ID`. Condicionar el panel a esa
> clave lo habría ocultado para todos. Se usa `IS_AUTHENTICATED` para la
> condición y `USER_EMAIL` como clave de caché de SPEC-S18-E1, que hasta ahora
> recibía siempre `None` y por tanto **no segmentaba por usuario**: dos sesiones
> distintas podían compartir respuesta cacheada, con riesgo para RN5.
- **Prioridad**: P1
- **Estado**: `[x]` | **Verificado**: 2026-09-04

---

## 3. Fuera de alcance (aceptado como deuda)

| Hallazgo | Motivo |
|----------|--------|
| **H21** — `DisponibilidadRead` con dos audiencias | 6 campos siguen siendo legibles. *Extract Class* prematuro; revisar si supera 8-10 campos. |
| **H22** — Sin tests automatizados de la capa GUI | Limitación estructural de Streamlit. Requeriría `AppTest` o Playwright: es un milestone propio, no un item de deuda. |
| **H5** — PII (correo) en logs de auditoría | DIVERGENCIA JUSTIFICADA: es trazabilidad operativa deliberada, con rotación de logs configurada. |

---

## 4. Riesgos y Mitigaciones

| Riesgo | Impacto | Mitigación |
|--------|---------|------------|
| B2 (clase base GUI) rompe llamadas en producción | **Alto** — toca los 4 servicios | Refactor puro: las firmas públicas no cambian. Ejecutar la suite tras cada servicio migrado, un commit por servicio. |
| B3 altera el flujo de autenticación | Alto | `get_empleado_actual()` conserva su contrato (lanza 401). Los tests de auth son la red de seguridad. |
| Refactor mezclado con feature | Medio | Regla explícita: ningún SPEC de este plan añade funcionalidad. Commits separados. |
| C1 revela cobertura muy por debajo del 80% | Medio | Documentar la brecha real; no inflar con tests triviales. Alimentaría un PLAN_11. |

---

## 5. Orden de Ejecución Sugerido

1. **C1** primero — sin medición de cobertura no hay forma de comprobar que los refactors no pierden verificación.
2. **A1 + A2** — cambios pequeños y acotados, ganancia inmediata de consistencia.
3. **B1** — el de menor riesgo entre los de duplicación.
4. **B3** — toca autenticación; hacerlo con la suite estable.
5. **B2** — el de mayor superficie; dejarlo último y avanzar servicio por servicio.
6. **C2** — en cuanto el usuario confirme la composición de BRIGITH.

---

## 6. Criterio de Cierre del Milestone

- [ ] SPECs A1, A2, B1, B2, B3, C1 y D1 marcados `[x]` con commit asociado.
- [ ] C2 resuelto o formalmente reasignado si la decisión sigue pendiente.
- [ ] `pytest -x` verde, sin regresión sobre los 76 tests actuales.
- [ ] `ruff check` y `mypy src` limpios.
- [ ] Cobertura medida y registrada en `CLAUDE.md`.
- [ ] AUDIT_12 con tasa SDD neta **≥ 85%**.
