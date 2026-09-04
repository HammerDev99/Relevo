# PLAN_09 — Milestone v8 "Alta de Usuarios en GUI y Visibilidad de Ausencias"

| Campo | Valor |
|-------|-------|
| **Fecha** | 2026-09-04 |
| **Fase CDAID** | Plan |
| **Milestone** | v8 |
| **Origen** | Solicitud del usuario (sesión 2026-09-04) tras alta manual de 3 empleados por consola en el VPS |
| **Objetivo** | (1) Cerrar la brecha de gestión de personal: permitir el alta de empleados desde el panel de Coordinación, eliminando la necesidad de operar la base de datos por consola. (2) Reformular RN5 para que el calendario muestre el nombre de quien está ausente a los usuarios autenticados. |

---

## 1. Estado Previo / Contexto

### 1.1 Brecha funcional: alta de usuarios

El CRUD de personal está **incompleto**. La API expone tres de las cuatro operaciones:

| Operación | Endpoint | Estado |
|-----------|----------|--------|
| Listar | `GET /coordinacion/usuarios` | ✅ Existe |
| Actualizar (rol, activo, grupos) | `PATCH /coordinacion/usuarios/{id}` | ✅ Existe |
| Eliminar | `DELETE /coordinacion/usuarios/{id}` | ✅ Existe |
| **Crear** | `POST /coordinacion/usuarios` | ❌ **No existe** |

**Consecuencia observable**: el 2026-09-04 el alta de tres empleados (DANIELREVOLLO, MARIANA, ROSA) tuvo que ejecutarse mediante un script Python en la consola del contenedor `relevo-api` del VPS. Esto implica acceso directo al volumen SQLite de producción, sin validación de entrada, sin trazabilidad y con riesgo de corrupción de permisos del archivo `.db` si se omite `gosu relevo`.

**Asimetría de riesgo**: existe `DELETE` sin su `POST` correspondiente. Un borrado accidental desde la GUI no puede deshacerse desde la aplicación.

**Activo reutilizable**: la pestaña *Grupos* del mismo panel ya implementa el patrón completo de alta (`st.expander` → `service.crear_grupo()` → `POST /coordinacion/grupos`). La Fase B replica ese patrón; no introduce arquitectura nueva.

### 1.2 Cambio de contrato: RN5

RN5 vigente hasta este planning:

> **RN5 — Privacidad**: el dato sensible (nombre, motivo) jamás se expone públicamente. Los empleados no ven quién ni por qué.

El usuario requiere que el calendario muestre el nombre de quien solicita la ausencia, al pasar el cursor sobre un día ocupado. Esto **contradice RN5 tal como está redactada**.

La restricción está implementada en tres capas:

| Capa | Mecanismo |
|------|-----------|
| Contrato | `CLAUDE.md` regla crítica 4 + tabla de reglas de negocio |
| Schema | `DisponibilidadRead` expone `grupos_ausentes` (nombres de grupo), nunca de persona |
| Test | `tests/v1/test_disponibilidad.py::test_disponibilidad_sin_pii` |

**Decisión tomada (2026-09-04)**: RN5 **se reformula, no se deroga**. Ver §3.

---

## 2. SPECs de Implementación (Milestone v8)

> **Orden de ejecución**: Fase B antes que Fase A. La Fase B no tiene decisiones pendientes y elimina de inmediato la operación manual por consola.

### Fase B — Alta de Usuarios desde el Panel de Coordinación (P0)

#### SPEC-S18-B1: Schema `UsuarioCreate`
- **Descripción**: Añadir el DTO de entrada para el alta de empleados.
- **Archivos**: `src/app/schemas/usuarios.py`
- **Criterios de Aceptación**:
    - [ ] `UsuarioCreate` con campos: `nombre: str`, `correo: EmailStr`, `password: str`, `rol: str = "empleado"`, `grupo_ids: list[int] = []`.
    - [ ] `model_config = ConfigDict(frozen=True)` — inmutabilidad (regla crítica 1).
    - [ ] Validación de longitud mínima de contraseña (8 caracteres).
    - [ ] Validación de `rol` restringido a `empleado` / `coordinacion`.
- **Prioridad**: P0
- **Estado**: `[ ]`

#### SPEC-S18-B2: Endpoint `POST /coordinacion/usuarios`
- **Descripción**: Crear el endpoint de alta, protegido por `get_coordinador`, reutilizando el patrón de `crear_grupo`.
- **Archivos**: `src/app/routes/coordinacion.py` (sección "Gestión de Usuarios")
- **Criterios de Aceptación**:
    - [ ] Requiere rol coordinación (`Depends(get_coordinador)`); un empleado recibe 403.
    - [ ] Contraseña almacenada con `get_password_hash()`; nunca en claro.
    - [ ] Correo duplicado → HTTP 400 con mensaje claro (no `IntegrityError` sin capturar).
    - [ ] `grupo_ids` asigna la relación M:N reutilizando el patrón de `actualizar_usuario`.
    - [ ] Responde `UsuarioRead` (sin `password_hash`).
- **Prioridad**: P0
- **Estado**: `[ ]`

#### SPEC-S18-B3: Método `crear_usuario()` en el servicio GUI
- **Descripción**: Añadir el cliente HTTP, calcado de `crear_grupo()`.
- **Archivos**: `src/app/gui/services/coordinacion_service.py`
- **Criterios de Aceptación**:
    - [ ] Decorado con `@log_gui_action("CoordinacionService")`, consistente con los métodos vecinos.
    - [ ] Propaga el `detail` del error al usuario mediante `st.error` (p. ej. correo duplicado).
    - [ ] Retorna `bool` como el resto de métodos del servicio.
- **Prioridad**: P0
- **Estado**: `[ ]`

#### SPEC-S18-B4: Formulario de alta en la pestaña *Personal de la Oficina*
- **Descripción**: Añadir el expander de alta, replicando el de *Crear Nuevo Grupo*.
- **Archivos**: `src/app/gui/pages/03_coordinacion.py` (`tab_users`)
- **Criterios de Aceptación**:
    - [ ] Expander "Registrar Nuevo Empleado" al inicio de `tab_users`, antes del listado.
    - [ ] Campos: nombre, correo, contraseña (`type="password"`), rol (`selectbox`), grupos (`multiselect`).
    - [ ] Reutiliza `opciones_grupos`, ya calculado en la pestaña.
    - [ ] Tras el alta exitosa: `st.success` + `st.rerun()`.
- **Prioridad**: P0
- **Estado**: `[ ]`

#### SPEC-S18-B5: Tests de alta de usuarios
- **Archivos**: `tests/v1/test_coordinacion.py`
- **Criterios de Aceptación**:
    - [ ] Success: coordinación crea empleado → 200, persiste, hash verificable con `verify_password`.
    - [ ] Success: alta con `grupo_ids` asigna correctamente la relación M:N.
    - [ ] Failure: correo duplicado → 400.
    - [ ] Failure: empleado sin rol coordinación → 403.
    - [ ] Failure: contraseña menor a 8 caracteres → 422.
    - [ ] `pytest -x` sin regresión (60 tests previos).
- **Prioridad**: P0
- **Estado**: `[ ]`

### Fase A — Visibilidad de Nombres en el Calendario (P1)

#### SPEC-S18-A1: Reformular RN5 y exponer nombres a usuarios autenticados
- **Descripción**: Añadir `empleados_ausentes` a la respuesta de disponibilidad, poblado **solo** si hay sesión válida.
- **Archivos**: `src/app/schemas/disponibilidad.py`, `src/app/routes/disponibilidad.py`
- **Criterios de Aceptación**:
    - [ ] `DisponibilidadRead` incorpora `empleados_ausentes: list[str] = []`.
    - [ ] Con sesión válida: contiene los nombres de los ausentes del día.
    - [ ] **Sin sesión: lista vacía**. El endpoint no requiere autenticación, por lo que los nombres nunca deben viajar a un cliente no autenticado.
    - [ ] **No se expone `tipo` ni `justificacion`** — solo el nombre.
    - [ ] Se reutiliza el `selectinload(Solicitud.empleado)` ya presente; sin consultas nuevas.
- **Prioridad**: P1
- **Estado**: `[ ]`

#### SPEC-S18-A2: Mostrar nombres en el tooltip del calendario
- **Descripción**: Extender el tooltip existente (SPEC-S15-C5) para incluir nombres.
- **Archivos**: `src/app/gui/pages/02_disponibilidad.py`
- **Criterios de Aceptación**:
    - [ ] El `title` del día ocupado incluye los nombres cuando `empleados_ausentes` no está vacío.
    - [ ] Se preserva el comportamiento actual de `grupos_ausentes` y del flag `mostrar_grupos_tooltip`.
    - [ ] Los nombres se escapan como HTML (el tooltip se inyecta con `unsafe_allow_html`).
    - [ ] Días festivos y fines de semana no muestran nombres.
- **Prioridad**: P1
- **Estado**: `[ ]`

#### SPEC-S18-A3: Actualizar el contrato RN5 en la documentación
- **Archivos**: `CLAUDE.md`, `README.md`, `agent_docs/reglas_concurrencia.md`, `agent_docs/architecture.md`
- **Criterios de Aceptación**:
    - [ ] `CLAUDE.md`: RN5 y la regla crítica 4 reflejan la nueva redacción de §3.
    - [ ] Se documenta la fecha y el motivo del cambio de contrato (trazabilidad).
    - [ ] `README.md` y `agent_docs/` quedan consistentes con el nuevo alcance.
- **Prioridad**: P1
- **Estado**: `[ ]`

#### SPEC-S18-A4: Reemplazar el test de PII por el test del nuevo contrato
- **Archivos**: `tests/v1/test_disponibilidad.py`
- **Criterios de Aceptación**:
    - [ ] `test_disponibilidad_sin_pii` se **reformula**, no se elimina: sigue verificando que **sin sesión** la respuesta no contiene nombres.
    - [ ] Test nuevo: **con sesión**, `empleados_ausentes` contiene los nombres esperados.
    - [ ] Test nuevo: la respuesta **nunca** contiene la justificación, ni con sesión.
- **Prioridad**: P1
- **Estado**: `[ ]`

---

## 3. Decisión de Diseño: reformulación de RN5

**Contexto**: el usuario requiere ver quién está ausente al pasar el cursor sobre un día del calendario. RN5 lo prohibía explícitamente.

**Opciones evaluadas** (sesión 2026-09-04):

| Opción | Descripción | Resultado |
|--------|-------------|-----------|
| A | Solo coordinación ve nombres | Descartada |
| B | Nombres visibles para todos | **Elegida**, acotada por las decisiones de alcance |
| C | Cada quien ve solo su propio nombre | Descartada |

**Decisiones de acotación** (misma sesión):

| Pregunta | Decisión |
|----------|----------|
| ¿Qué datos se exponen? | **Solo nombre**. Tipo y justificación permanecen protegidos. |
| ¿A quién? | **Solo a usuarios con sesión iniciada**. Sin sesión, se mantiene la vista por grupos. |

**RN5 — redacción vigente a partir de PLAN_09**:

> **RN5 — Privacidad**: la justificación y el tipo de ausencia jamás se exponen a terceros. Los nombres de los empleados ausentes son visibles **únicamente para usuarios autenticados**; la vista sin sesión sigue mostrando solo estados derivados y nombres de grupo.

**Justificación de la acotación**: el endpoint `/disponibilidad` responde sin autenticación. Exponer nombres sin condicionar a sesión los haría accesibles a cualquier cliente que alcance la URL dentro de la red. La justificación del permiso (salud, familia, asuntos personales) es el dato de mayor sensibilidad bajo la Ley 1581/2012 y queda fuera del cambio.

**Riesgo aceptado**: los nombres de ausencias pasan a ser visibles entre compañeros de la dependencia. Es una decisión del responsable del sistema, tomada de forma explícita y registrada aquí para trazabilidad.

---

## 4. Riesgos y Mitigaciones

| Riesgo | Impacto | Mitigación |
|--------|---------|------------|
| Contraseña inicial débil o compartida | Alto | Longitud mínima 8 en el schema; el empleado la cambia en *Mi Perfil* |
| Alta de un segundo coordinador por error | Medio | `rol` por defecto `empleado`; el `selectbox` exige acción deliberada |
| Nombres filtrados a clientes sin sesión | Alto | SPEC-S18-A1 condiciona a sesión; SPEC-S18-A4 lo verifica con test |
| Inyección HTML vía nombre en el tooltip | Medio | Escape HTML explícito (SPEC-S18-A2) |
| Regresión en los 60 tests existentes | Medio | TDD por SPEC; `pytest -x` + `ruff check` en cada paso |

---

## 5. Deuda técnica pendiente (fuera de alcance)

| Item | Origen | Prioridad |
|------|--------|-----------|
| Rotación de la contraseña de coordinación (`admin123`) en producción | `CREDENCIALES_PRUEBA.md` — pendiente desde el paso a producción (v6) | **P0 — vencida** |
| `scripts/crear_empleados.py` queda como herramienta de contingencia | Sesión 2026-09-04 | P2 |
| BRIGITH sin grupo asignado vs. `CREDENCIALES_PRUEBA.md` que la lista en G3 | Discrepancia detectada 2026-09-04 | P2 |

---

## 6. Criterio de Cierre del Milestone

- [ ] Los 9 SPECs marcados `[x]` con commit asociado.
- [ ] `pytest -x` verde; sin regresión sobre los 60 tests previos.
- [ ] `ruff check src tests scripts` limpio.
- [ ] Alta de un empleado verificada de extremo a extremo desde la GUI.
- [ ] Documentación sincronizada con la nueva RN5.
- [ ] AUDIT_11 con veredicto APROBADO (tasa SDD ≥ 85%).
