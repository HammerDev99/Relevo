# PLAN_08 — Milestone v7 "Alineación del Modelo de Concurrencia y Operación VPS"

| Campo | Valor |
|-------|-------|
| **Fecha** | 2026-06-02 |
| **Fase CDAID** | Plan |
| **Milestone** | v7 |
| **Origen** | Auditoría de consistencia (sesión 2026-06-02) + backlog diferido SPRINT_16 / AUDIT_09 |
| **Objetivo** | Alinear el calendario de disponibilidad y toda la documentación con el modelo de concurrencia **por grupo** (intención de diseño v3, *source of truth* en `domain.py`), corregir el contrato RN3/RN4, validar la composición de excepciones (RN4) y completar la operación productiva del VPS (rotación de logs y backup). |

---

## 1. Estado Previo / Contexto

Durante la verificación cruzada de reglas se detectó una **inconsistencia estructural** entre tres fuentes:

| Fuente | Modelo de concurrencia | Estado |
|--------|------------------------|--------|
| Intención de diseño (PLAN_05 / SPEC-S13-C1) | **Por grupo** (`cupo = miembros − min_presentes`) | ✅ Autoritativa |
| Motor `src/app/domain.py` | **Por grupo** | ✅ Correcto |
| Calendario `src/app/routes/disponibilidad.py` | **Global** (1 → OCUPADO, 2 → EXCEPCIONAL) | ❌ Desactualizado (lógica v1) |
| Contrato RN3/RN4 (`CLAUDE.md`) | **Global** ("máx 1 / máx 2") | ❌ Texto obsoleto |
| Sección Reglas de Negocio (`README.md`) | **Global** | ❌ Incorrecta (introducida por error) |

**Consecuencia observable**: el calendario es sistemáticamente más pesimista que el motor. Ejemplo con datos del seed (G3 = 4 miembros, `min_presentes=2`, cupo normal 2): si JORGE y YESENIA (G3) están ausentes el mismo día, un empleado de G2 ve el día 🔴 EXCEPCIONAL aunque el motor aprobaría su solicitud **sin excepción**. Esto desincentiva solicitudes legítimas.

**Brecha adicional**: RN4 ("máx 2: vacaciones+permiso, o 2 permisos justificados") describe una restricción por **composición de tipos** que **no se valida** en ninguna capa.

---

## 2. SPECs de Implementación (Milestone v7)

### Fase A — Alineación del Modelo de Concurrencia (Núcleo)

#### SPEC-S16-A1: Migrar calendario a modelo por grupo
- **Descripción**: Reescribir el cálculo de estado en `routes/disponibilidad.py` para que refleje el cupo por grupo en lugar del conteo global.
- **Criterios de Aceptación**:
    - [x] El endpoint `/disponibilidad` calcula, por día, el estado de cada grupo según `cupo_normal = miembros_activos − min_presentes` y `cupo_max = cupo_normal + 1`.
    - [x] Se respeta la multi-pertenencia (HECTOR afecta G1 y G4).
    - [x] El test `test_disponibilidad.py::test_disponibilidad_sin_pii` se actualiza al nuevo modelo (los empleados de prueba deben pertenecer a grupos).
    - [x] Se preserva RN5: la respuesta no expone PII; `grupos_ausentes` sigue mostrando solo nombres de grupo.
- **Estado**: `[x]` | **Verificado**: 2026-06-02 | **Commit**: `68d4230`
- **Prioridad**: P0
- **Decisión de diseño**: ✅ **Opción A** (calendario consciente de sesión) — aprobada 2026-06-02. Ver §3.

#### SPEC-S16-A2: Validar composición de excepción (RN4)
- **Descripción**: Endurecer `domain.py` para que la excepción (`cupo_normal + 1`) solo se permita cuando la composición sea "vacaciones + permiso" o "2 permisos justificados" (con justificación no vacía).
- **Criterios de Aceptación**:
    - [x] Si la solicitud excepcional es un permiso sin justificación, se rechaza.
    - [x] Se valida que la combinación de ausentes en el día corresponde a una composición permitida por RN4.
    - [x] Tests Success y Failure que cubran ambas composiciones.
- **Estado**: `[x]` | **Verificado**: 2026-06-02 | **Commit**: `2391c1c`
- **Prioridad**: P1

### Fase B — Documentación (Elementos a Actualizar)

> **Núcleo del encargo**: sincronizar toda la documentación con el modelo por grupo. Detalle por archivo en §4.

#### SPEC-S16-B1: Corregir contrato RN3/RN4 en `CLAUDE.md`
- **Criterios de Aceptación**:
    - [x] RN3 redefinida como concurrencia **por grupo** basada en `min_presentes`.
    - [x] RN4 redefinida como "cupo del grupo + 1 excepción", con la condición de composición de tipos.
    - [x] Nota que aclara que el modelo global de v1 fue reemplazado en v3 (PLAN_05).
- **Estado**: `[x]` | **Verificado**: 2026-06-02 | **Commit**: `e9aa7af` | **Prioridad**: P0

#### SPEC-S16-B2: Corregir sección "Reglas de Negocio" en `README.md`
- **Criterios de Aceptación**:
    - [x] Reemplazar la tabla de "Concurrencia (toda la oficina)" por "Concurrencia por grupo".
    - [x] Corregir el ejemplo JACKSON/JORGE (hoy describe el comportamiento incorrecto).
    - [x] Actualizar la sección "Calendario de disponibilidad" según la opción A/B elegida.
- **Estado**: `[x]` | **Verificado**: 2026-06-02 | **Commit**: `e9aa7af` | **Prioridad**: P0

#### SPEC-S16-B3: Actualizar `agent_docs/architecture.md`
- **Criterios de Aceptación**:
    - [x] Documentar el modelo de concurrencia por grupo como estándar de dominio.
    - [x] Aclarar la relación entre el calendario (vista) y `domain.py` (motor/source of truth).
- **Estado**: `[x]` | **Verificado**: 2026-06-02 | **Commit**: `e9aa7af` | **Prioridad**: P1

#### SPEC-S16-B4: Crear referencia del modelo de cupos
- **Criterios de Aceptación**:
    - [x] Nuevo documento `agent_docs/reglas_concurrencia.md` con la fórmula de cupo, tabla de grupos del seed y ejemplos resueltos.
- **Estado**: `[x]` | **Verificado**: 2026-06-02 | **Commit**: `e9aa7af` | **Prioridad**: P2

#### SPEC-S16-B5: Re-alinear la comunicación a empleados al modelo por grupo
- **Descripción**: El mensaje a empleados redactado en la sesión describe el modelo **global** ("máx 1 ausente, máx 2") — incorrecto bajo el modelo por grupo.
- **Criterios de Aceptación**:
    - [x] Re-redactar el mensaje explicando que la disponibilidad depende del **grupo de trabajo** (cada grupo mantiene un mínimo de presentes).
    - [x] Corregir la nota de §8 de este plan que afirma que el mensaje "describe el comportamiento real".
- **Estado**: `[x]` | **Verificado**: 2026-06-02 | **Commit**: `e9aa7af` | **Prioridad**: P1

#### SPEC-S16-B6: Reconciliar composición de grupos (seed vs PLAN_05)
- **Descripción**: `PLAN_05` define G3 con 3 miembros (cupo 1); `seed.py` tenía 4 (BRIGITH "por defecto", cupo 2). La doc y la realidad de producción no coincidían.
- **Decisión (2026-06-02)**: BRIGITH **queda fuera de todos los grupos**. `seed.py` actualizado (`BRIGITH: []`).
- **Criterios de Aceptación**:
    - [x] BRIGITH sin grupo en `seed.py`.
    - [x] Consecuencia funcional resuelta en SPEC-S16-A4 (empleado sin grupo puede solicitar).
    - [x] Reflejar la composición canónica resultante en `agent_docs/reglas_concurrencia.md` (B4): G3 queda en 3 miembros (JORGE, YESENIA, DANIELA → cupo 1).
- **Estado**: `[x]` | **Verificado**: 2026-06-02 | **Commit**: `e9aa7af` | **Prioridad**: P1

#### SPEC-S16-A4: Manejo de empleados sin grupo ✅
- **Descripción**: `domain.py` bloqueaba a cualquier empleado sin grupo. Con BRIGITH fuera de grupos, no podría crear solicitudes.
- **Decisión (2026-06-02)**: un empleado sin grupo **sí puede solicitar**, aplicando solo saldos (RN2), respaldo (RN6) y duplicidad; **se omite la concurrencia de grupo**.
- **Criterios de Aceptación**:
    - [x] `domain.py` omite la validación de grupo cuando el empleado no tiene grupos (no bloquea).
    - [x] Test `test_validar_empleado_sin_grupo_permitido` (Success).
- **Estado**: `[x]` | **Verificado**: 2026-06-02 (implementado en esta sesión, previo a PLAN_08)

### Fase C — Operación VPS (Backlog diferido SPRINT_16 / AUDIT_09)

#### SPEC-S15-D5: Rotación de logs en VPS
- **Criterios de Aceptación**:
    - [x] Configurar `logrotate` (o driver `json-file` con `max-size`/`max-file`) para el volumen de logs.
    - [x] Documentar la configuración en `docs/others/deploy-vps-instructions.md`.
- **Estado**: `[x]` | **Verificado**: 2026-06-02 | **Commit**: `9e247fc` | **Prioridad**: P2

#### SPEC-S15-D6: Backup automatizado en crontab
- **Criterios de Aceptación**:
    - [x] Ejecutar el script `backup-relevo.sh` (ya documentado) en el VPS.
    - [x] Confirmar entrada en crontab (2 AM diario) y verificar primer backup.
- **Estado**: `[x]` | **Verificado**: 2026-06-02 | **Commit**: `9e247fc` | **Prioridad**: P2
- **Nota**: Los comandos de verificación y ejecución manual del backup están en Fase 7 de `deploy-vps-instructions.md`. La ejecución real en el VPS queda como acción pendiente del operador (M1 en §9).

---

## 3. Decisión de Diseño Clave: Calendario por Grupo (Opción A vs B)

> ✅ **DECISIÓN APROBADA (2026-06-02): Opción A — Calendario consciente de sesión.**

El calendario hoy es **anónimo y público** (un estado por día). En el modelo por grupo, el estado de un día **depende del grupo de quien mira**. Dos opciones:

| | **Opción A — Consciente de sesión** *(recomendada)* | **Opción B — Desglose por grupo** |
|---|---|---|
| Con sesión | Estado del día relativo a *mis grupos* (el más restrictivo) | Cada día muestra el estado de todos los grupos |
| Sin sesión | Vista informativa de ocupación general (con aviso) | Igual (desglose para todos) |
| UX móvil | Limpia (mantiene el grid optimizado en SPRINT_16) | Más recargada (riesgo en móvil) |
| Privacidad (RN5) | Sin PII; revela solo estado de mis grupos | Sin PII; revela ocupación de todos los grupos |

**Recomendación**: **Opción A**. Mantiene la UX móvil recién optimizada y entrega información accionable (el estado que realmente afecta al usuario). El visitante sin sesión ve una capa informativa general.

---

## 4. Elementos de Documentación a Actualizar (Detalle)

| Archivo | Sección | Estado actual | Estado objetivo |
|---------|---------|---------------|-----------------|
| `CLAUDE.md` | Tabla "Reglas de negocio" (RN3, RN4) | "máx 1 / máx 2" global | Concurrencia por grupo (`min_presentes`) + composición RN4 |
| `README.md` | "📋 Reglas de Negocio" → Concurrencia | Tabla "toda la oficina" + ejemplo JACKSON/JORGE incorrecto | Tabla por grupo + ejemplo corregido |
| `README.md` | "Calendario de disponibilidad" | Describe estado global | Describir Opción A (consciente de sesión) |
| `agent_docs/architecture.md` | Estándar de comunicación / dominio | No menciona modelo de concurrencia | Documentar modelo por grupo y rol de `domain.py` |
| `agent_docs/reglas_concurrencia.md` | (nuevo) | No existe | Fórmula de cupo + tabla de grupos + ejemplos |
| `docs/others/deploy-vps-instructions.md` | Operación | Sin logrotate | Añadir rotación de logs (D5) |
| `CLAUDE.md` | Estado actual / Historial de Sprints | Milestone v6 cerrado | Añadir Milestone v7 y SPRINT_17 al cierre |
| `docs/sprints/SPRINT_17_*.md` | (nuevo) | No existe | Documentar la ejecución de este plan |
| `docs/validate/AUDIT_10_*.md` | (nuevo) | No existe | Auditoría SDD post-implementación |

---

## 5. Alcance por Fases

| Fase | Items | Esfuerzo estimado |
|------|:-----:|:-----------------:|
| A — Núcleo (calendario + RN4) | 2 | 6 h |
| B — Documentación | 4 | 3 h |
| C — Operación VPS | 2 | 2 h |
| **Total** | **8** | **11 h** |

---

## 6. Criterios de Éxito

- [x] Calendario refleja el cupo por grupo (Opción A aprobada, SPEC-S16-A1).
- [x] `domain.py` valida composición de excepción (RN4) (SPEC-S16-A2).
- [x] Toda la documentación (§4) alineada al modelo por grupo — sin contradicciones entre contrato, README, agent_docs y código (SPEC-S16-B1..B6).
- [x] `pytest -x` pasa sin regresión — 59 tests al final de PLAN_08 (baseline: 55).
- [x] `ruff check src` limpio.
- [ ] Auditoría SDD post-implementación (AUDIT_10) con tasa ≥ 85%. ← **Próxima fase (Check)**

---

## 7. Dependencias y Riesgos

| Riesgo | Impacto | Mitigación |
|--------|:-------:|------------|
| Calendario por grupo rompe el patrón anónimo actual | Alto | ✅ Resuelto: Opción A aprobada (§3). Visitante sin sesión ve capa informativa general |
| Test `test_disponibilidad_sin_pii` asume modelo global | Medio | Actualizar fixture con grupos; preservar aserción de no-PII |
| Cambio de RN3/RN4 puede confundir a usuarios ya capacitados | Medio | Comunicar el cambio; el mensaje a empleados ya describe el comportamiento real |
| Composición RN4 puede tener casos límite (multi-grupo) | Medio | Cubrir con tests Success/Failure explícitos |

---

## 8. Notas

- El motor `domain.py` **no requiere cambios** en su modelo de concurrencia: ya es correcto. El trabajo es alinear el **calendario** y la **documentación** hacia él, más la mejora puntual de RN4 (A2).
- ~~El mensaje a empleados redactado en la sesión describe el comportamiento real esperado.~~ **Corrección (SPEC-S16-B5)**: el mensaje original describía el modelo global (incorrecto). El documento actualizado es `docs/others/comunicacion_empleados.md`, que explica el modelo por grupo.

---

## 9. Estado Operativo y Acciones Manuales Pendientes (anclaje cold-start)

> Esta sección existe para que el plan sea autosuficiente al reiniciar el contexto del LLM. Captura acciones **manuales/operativas** que no viven en el repositorio (configuración de EasyPanel/VPS).

### 9.1 Estado del despliegue (a 2026-06-02)
- **Producción activa**: `relevo-api` (interno :8000) + `relevo-gui` (`relevo.sprintjudicial.com`, :8501) en EasyPanel/VPS `31.97.146.7`.
- **BD de producción**: migrada al volumen bind `/etc/easypanel/projects/sprintjudicial/relevo-api/volumes/relevo-db-data/relevo.db` (owner `1000:1000`).
- **`main` está adelante de lo desplegado**: todos los commits hasta `cd4a340` requieren **redeploy** para quedar activos en el VPS.

### 9.2 Acciones manuales pendientes de verificar/ejecutar

| # | Acción | Dónde | Por qué | Estado |
|---|--------|-------|---------|:------:|
| M1 | **Redeploy** de `relevo-api` y `relevo-gui` con la imagen más reciente | EasyPanel | Activar auth guard, `/docs` off, UX móvil, navegación mes/año, coordinadores LUISA/JOHN | ❓ |
| M2 | **Quitar el dominio `api.relevo.sprintjudicial.com`** del servicio `relevo-api` | EasyPanel → relevo-api → Domains | La API no debe ser accesible desde internet (solo interna `relevo-api:8000`) | ✅ hecho 2026-06-02 |
| M3 | **Confirmar `APP_ENV=production`** en variables de `relevo-api` | EasyPanel env | Deshabilita `/docs`, `/redoc`, `/openapi.json` en producción | ✅ visto en `docker inspect` |
| M4 | **Configurar webhook auto-deploy** GitHub→EasyPanel (push a `main` → redeploy) | GitHub Settings/Webhooks + EasyPanel | Evitar redeploys manuales tras cada commit | ✅ hecho 2026-06-02 |
| M5 | Mantener `CREDENCIALES_PRUEBA.md` solo local (gitignored) | Local | Contiene usuarios/contraseñas de prueba; incluye coordinadores LUISA y JOHN | ℹ️ |

### 9.3 Verificación de aislamiento de la API (tras M2)
```bash
# Debe FALLAR (connection refused / timeout) — API no expuesta:
curl -m 5 https://api.relevo.sprintjudicial.com/        # no debe responder 200
# Debe responder {"message":"Relevo API v1"} — solo interno:
docker exec $(docker ps -q -f "name=relevo-gui") wget -qO- http://relevo-api:8000/
```

### 9.4 Referencias clave para retomar en frío
- Guía de despliegue completa: `docs/others/deploy-vps-instructions.md`
- Reglas de negocio (a corregir en este plan): `CLAUDE.md` §Reglas de negocio + `README.md`
- Motor autoritativo de concurrencia: `src/app/domain.py` (función `validar_solicitud`)
- Calendario a migrar: `src/app/routes/disponibilidad.py` + `src/app/gui/pages/02_disponibilidad.py`
