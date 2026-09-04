# AUDIT_12 — GATE v9 Deuda Técnica y Consistencia (PLAN_10 / SPRINT_19)

| Campo | Valor |
|-------|-------|
| **Fecha** | 2026-09-04 |
| **Fase CDAID** | Check |
| **Milestone** | v9 |
| **Sprint** | SPRINT_19 |
| **Auditor** | Multi-agente SDD v2 (security-auditor, code-reviewer, architect) + skills `/refactoring` y `/design-patterns` |
| **Alcance** | 8 SPECs: A1–A2 (roles), B1–B3 (duplicación), C1–C2 (verificación y consistencia), D1 (alcance del panel táctil) |
| **Resultado** | **APROBADO** |

---

## 1. Consistencia Planning ↔ Sprint

| Fuente | SPECs `[x]` | Estado |
|--------|:-----------:|--------|
| `PLAN_10` | 8 de 8 | Sin pendientes |
| `SPRINT_19` | 8 de 8 | ✅ Done |

**Sin inconsistencias.** Ambos documentos coinciden en alcance, numeración y estado.

---

## 2. Baseline Técnico

| Herramienta | Resultado |
|-------------|-----------|
| **Pytest** | ✅ 78 passed (76 previos + 2 nuevos, sin regresión) |
| **Ruff** | ✅ All checks passed (`src tests scripts`) |
| **Mypy** | ✅ Success — 45 archivos, sin errores |
| **Cobertura** | ✅ **88%** (657 líneas verificables) |
| **Repo** | `main` = `origin/main`, working tree limpio |

> Primera auditoría del proyecto con los cuatro indicadores en verde simultáneamente.

---

## 3. Hallazgos por agente

### Security Auditor

| ID | Archivo | Hallazgo | Clasificación SDD |
|----|---------|----------|-------------------|
| H1 | `roles.py` | La whitelist `Literal` cierra el vector de A1: un `PATCH` con rol arbitrario es rechazado por Pydantic **antes** de tocar la BD. Verificado con test RED previo al fix | **CONFORME** |
| H2 | `auth.py:38-72` | `get_empleado_opcional()` **no degrada** la seguridad: aplica las mismas tres comprobaciones (token presente, sesión válida, empleado activo). `get_empleado_actual()` solo añade el rechazo, de modo que ningún endpoint protegido pierde validación | **CONFORME** |
| H3 | `base_service.py:29-32` | `get_auth_headers()` lee el token de `session_state` y lo envía como cookie; no se registra ni se expone en mensajes | **CONFORME** |
| H4 | `base_service.py:65-67` | El `except` mostraba la excepción cruda al usuario (`f"...: {e}"`), pudiendo filtrar la URL interna `http://relevo-api:8000` en pantalla. Preexistente en los 19 bloques originales, pero ahora centralizado | **DEFECTO** |
| H5 | `auth.py:51` | Los tres mensajes 401 diferenciados ("No autenticado" / "Sesión inválida" / "Empleado inactivo") se consolidaron en uno. **Mejora de seguridad**: reduce la enumeración de estados de cuenta. Verificado que ningún test ni cliente dependía de la distinción | **CONFORME** |
| H6 | `seed.py` | Tras C2, ninguna credencial queda hardcodeada: la única cuenta del seed usa `RELEVO_SEED_PASSWORD` | **CONFORME** |

### Code Reviewer (skill `/refactoring`)

| ID | Archivo | Smell / Hallazgo | Clasificación SDD |
|----|---------|------------------|-------------------|
| H7 | `gui/services/*` | **Duplicate Code eliminado**: 19 bloques `httpx.Client` → 1. Los 4 servicios concretos bajan de 425 a 308 líneas (−28%). Técnica *Extract Superclass* correctamente aplicada | **CONFORME** |
| H8 | `base_service.py:34-46` | `_request()` tiene **9 parámetros** → **Long Parameter List**. Mitigado: todos salvo `metodo` y `ruta` son keyword-only con default, y cada uno representa un eje real de variación. *Introduce Parameter Object* sería peor remedio que enfermedad para 4 llamadores | **DIVERGENCIA JUSTIFICADA** |
| H9 | `base_service.py:30` | `from app.gui import session_keys` estaba **dentro** del método. Verificado que no existe ciclo de imports: el import local era un vestigio innecesario | **DEFECTO** (menor, de estilo) |
| H10 | `routes/coordinacion.py:17-24` | `_resolver_grupos()` documenta explícitamente que los ids inexistentes se ignoran — preserva el comportamiento previo en lugar de cambiarlo silenciosamente durante un refactor | **CONFORME** |
| H11 | `roles.py` | 17 líneas, responsabilidad única, sin dependencias. **Replace Magic String with Symbolic Constant** aplicado: 12 literales de rol → 0 fuera del módulo | **CONFORME** |
| H12 | `seed.py` | Tras C2 el comentario explica *por qué* se retiraron las tres cuentas y qué implica. Evita que un futuro mantenedor las reponga por descuido | **CONFORME** |
| H13 | `tests/v1/test_seed.py` | El test de conteo se ajustó a 11 registros. Correcto, pero es un test frágil: cualquier alta en el seed lo rompe. Aceptable como red de seguridad ante cambios no intencionados | **DIVERGENCIA MENOR** |

### Architect (skill `/design-patterns` — GoF + SOLID)

| ID | Ámbito | Hallazgo | Clasificación SDD |
|----|--------|----------|-------------------|
| H14 | `BaseAPIService` | **Template Method** parcial: la base define el flujo de transporte y las subclases aportan la semántica de cada endpoint. Los 4 servicios respetan **LSP** — ninguno redefine `__init__` ni altera el contrato | **CONFORME** |
| H15 | `auth.py` (B3) | **DIP restaurado**: `disponibilidad.py` dependía de su propia implementación de auth; ahora depende de la abstracción de `auth.py`. Cierra un hallazgo diferido por **dos auditorías** (AUDIT_10 H16 → AUDIT_11 H20) | **CONFORME** |
| H16 | `roles.py` | **OCP**: añadir un rol exige tocar un único módulo. Antes eran 8 archivos | **CONFORME** |
| H17 | `base_service.py` | Distingue explícitamente fallo de transporte (`None`) de respuesta con código de error (se devuelve). Decisión de diseño acertada: evita que la base imponga política de negocio a los servicios | **CONFORME** |
| H18 | `gui/services/` | Los servicios anidaban un `AuthService` interno solo para las cabeceras (**Middle Man**). Eliminado al subir `get_auth_headers()` a la base | **CONFORME** |
| H19 | `DisponibilidadRead` | Heredado de AUDIT_11 H21: 7 campos, dos audiencias. Sigue legible; *Extract Class* prematuro | **DIVERGENCIA MENOR** |
| H20 | Cobertura GUI | `[tool.coverage.run] omit` excluye `src/app/gui/*`. Decisión correcta y documentada, pero implica que **B2 y D1 no tienen verificación automatizada**: se validaron por inspección, mypy y prueba manual | **DIVERGENCIA JUSTIFICADA** |

---

## 4. Conformidad SDD (protocolo 8 puntos)

| Punto | Verifica | Resultado |
|-------|----------|-----------|
| **P1** | DTOs frozen, campos, JSON serializable | ✅ `UsuarioCreate`/`UsuarioUpdate` frozen; `RolUsuario` compartido |
| **P2** | Firmas, paths Success/Failure | ✅ A1 cubre ambos; refactors preservan firmas |
| **P3** | Backward compat | ✅ Ninguna firma pública cambió; sin migración de esquema |
| **P4** | DI/Container | ✅ `get_empleado_opcional` y `get_empleado_actual` como dependencias FastAPI |
| **P5** | Interfaces delegan correctamente | ✅ GUI → `BaseAPIService` → API; sin acceso directo a BD |
| **P6** | Tests Success/Failure y cobertura | ✅ 2 tests nuevos (1 Success, 1 Failure); refactors verificados por equivalencia; cobertura 88% |
| **P7** | Code smells | ✅ Duplicate Code y Middle Man eliminados; H8 justificado, H9 corregido |
| **P8** | Patterns | ✅ Extract Superclass, Template Method parcial, DIP restaurado, OCP en roles |

### Tasa de aprobación

| Clasificación | Cantidad |
|---------------|:--------:|
| CONFORME | 14 |
| DIVERGENCIA JUSTIFICADA | 2 |
| DIVERGENCIA MENOR | 2 |
| **DEFECTO** | **2** |
| **Total** | **20** |

**Tasa** = (14 + 2) / 20 = **80.0%** pre-corrección
**Tasa post-corrección** = (16 + 2) / 20 = **90.0%** ✅

> Supera el umbral del 85%. Comparativa: AUDIT_11 cerró en 84.2% neto; AUDIT_12 alcanza **90.0%** con el mismo instrumental (mismas skills, misma clasificación), lo que hace las cifras comparables. La mejora refleja que el sprint atacó precisamente la deuda que la auditoría anterior había expuesto.

---

## 5. Correcciones aplicadas (fase Act)

| ID | Defecto | Corrección | Verificación |
|----|---------|------------|--------------|
| H4 | Excepción cruda mostrada al usuario, con riesgo de filtrar la URL interna del API | El detalle técnico va a `logger.warning()` (regla crítica 3: `get_logger(__name__)`); la pantalla muestra "No se pudo conectar con el servidor." | 78 tests verdes; ruff y mypy limpios |
| H9 | Import local innecesario en `get_auth_headers()` | Movido a nivel de módulo tras comprobar que no hay ciclo de imports | `from app.gui.services.base_service import BaseAPIService` importa sin error |

Ambas correcciones son de bajo riesgo y quedan cubiertas por la suite existente.

---

## 6. Hallazgos diferidos (backlog → PLAN_11)

| ID | Hallazgo | Prioridad | Motivo del diferimiento |
|----|----------|:---------:|-------------------------|
| — | `routes/coordinacion.py` al **57%** de cobertura: los endpoints de solicitudes y grupos carecen de tests | **P1** | Requiere tests nuevos; este milestone era refactor |
| H13 | `test_seed.py` acopla el conteo exacto de registros | P3 | Frágil pero útil como red ante cambios no intencionados |
| H19 | `DisponibilidadRead` con dos audiencias (heredado AUDIT_11 H21) | P3 | 7 campos siguen legibles |
| H20 | Sin tests automatizados de la capa GUI (heredado AUDIT_11 H22) | P2 | Requiere `AppTest` o Playwright: milestone propio |
| — | `session_keys.USER_ID` declarado pero nunca escrito | P2 | Detectado en SPRINT_19; o se popula en el login o se elimina de `session_keys` |

---

## 7. Veredicto

**APROBADO** — Gate v9 superado con autoridad automática.

| Criterio | Requisito | Resultado |
|----------|-----------|-----------|
| Tasa SDD | ≥ 85% | **90.0%** ✅ |
| Defectos sin resolver | 0 | **0** ✅ |
| Regresión | ninguna | 78 tests, 0 fallos ✅ |

**Fundamento**:

1. **Los 8 SPECs cumplen sus criterios**, con planning y sprint consistentes.
2. **Refactors verificados por equivalencia**: B1, B2 y B3 pasan los tests existentes **sin modificarlos**, que es la prueba exigida por PLAN_10 §1.
3. **Deuda de AUDIT_11 saldada**: H8, H9, H14 y H20 de aquella auditoría quedan cerrados. H20 llevaba **dos auditorías** diferido.
4. **Capacidad de verificación recuperada** (C1): la regla del 80% de cobertura se venía afirmando sin medirla. Ahora es 88%, medida y reproducible.
5. **Tres hallazgos de ejecución** documentados en SPRINT_19 que ninguna auditoría previa había detectado: `USER_ID` sin poblar (con impacto real en la segmentación de caché y por tanto en RN5), cobertura no medible, y ausencia de timeouts HTTP.
6. Las divergencias menores no tienen impacto funcional y quedan en backlog con prioridad asignada.

**Nota metodológica**: la mejora de 84.2% a 90.0% es comparable porque se usó el mismo instrumental que AUDIT_11 (mismas skills, misma taxonomía). No obstante, el 88% de cobertura excluye la capa GUI, donde viven B2 y D1: su verificación fue por inspección y prueba manual, no automatizada (H20). Es la principal limitación de esta auditoría.
