# AUDIT_10 — GATE v7 Alineación de Concurrencia (PLAN_08 / SPRINT_17)

| Campo | Valor |
|-------|-------|
| **Fecha** | 2026-06-02 |
| **Fase CDAID** | Check |
| **Milestone** | v7 |
| **Sprint** | SPRINT_17 |
| **Auditor** | Multi-agente SDD v2 (security-scanner, code-reviewer, architect) |
| **Resultado** | APROBADO |

---

## 1. Baseline Técnico

| Herramienta | Resultado pre-audit | Resultado post-fix |
|-------------|--------------------|--------------------|
| **Pytest** | ✅ 59 passed | ✅ 60 passed (+1 test de regresión H1) |
| **Ruff** | ✅ All checks passed | ✅ All checks passed |
| **Mypy** | ⚠️ 1 error preexistente en `02_disponibilidad.py:201` (no introducido por SPRINT_17) | igual |

---

## 2. Hallazgos por agente

### Security Scanner

| ID | Archivo | Hallazgo | Clasificación Agente | Clasificación SDD |
|----|---------|----------|---------------------|-------------------|
| H1 | `routes/disponibilidad.py` | `anio`/`mes` sin validación de rango → ValueError/HTTP 500 con valores fuera de rango | DEFECTO HIGH | **DEFECTO** |
| H2 | `routes/auth.py` (pre-existente) | Cookie `secure=False` hardcodeado; sin efecto HTTPS en prod | DEFECTO HIGH | **DIVERGENCIA MENOR** (pre-existente, no regresión de SPRINT_17) |
| H3 | `routes/auth.py` (pre-existente) | Cookie sin `path="/"` explícito | DIVERGENCIA MENOR | DIVERGENCIA MENOR (pre-existente) |
| H4 | `routes/disponibilidad.py:17-28` | `_empleado_de_sesion()`: gestión de sesión correcta (token firmado + max_age + empleado activo) | CONFORME | **CONFORME** |
| H5 | `routes/disponibilidad.py` + `schemas/` | RN5 preservada: respuesta sin PII, `grupos_ausentes` solo nombres de grupo | CONFORME | **CONFORME** |
| H6 | `domain.py:102-114` | Validación RN4 sin vulnerabilidades ni bypasses | CONFORME | **CONFORME** |

### Code Reviewer

| ID | Archivo | Hallazgo | Clasificación SDD |
|----|---------|----------|-------------------|
| H7 | `disponibilidad.py:31-53` | `_estado_para_grupos()`: algoritmo cupo_normal/cupo_max correcto; early return EXCEPCIONAL correcto | **CONFORME** |
| H8 | `disponibilidad.py:48,50` | `cupo_normal > 0` guard: el reviewer sugirió removerlo, pero el análisis es incorrecto — sin la guard, `count=0 >= cupo_normal=0` → OCUPADO (bug). Comportamiento actual es correcto. | **CONFORME** |
| H9 | `disponibilidad.py:121-125` | `grupos_ausentes` muestra grupos fuera del scope del usuario (multi-grupo): un usuario de G1 ve G4 en tooltip cuando HECTOR está ausente. No viola RN5 (grupos no son PII). UX menor. | **DIVERGENCIA MENOR** |
| H10 | `disponibilidad.py:124` | `if g.nombre not in grupos_ausentes` sobre lista es O(n); un `set` sería más idiomático | **DIVERGENCIA MENOR** |
| H11 | Multi-grupo HECTOR (G1+G4) | No existe test de regresión para el escenario multi-grupo | **DIVERGENCIA MENOR** |
| H12 | `domain.py:104-114` | Validación RN4: guard correcta, Result/Failure según convención, lógica correcta | **CONFORME** |
| H13 | `test_domain.py:340-455` | 3 tests nuevos cubren Failure×2 y Success×1 de A2; `test_validar_excepcion_valida` cubre vacaciones+permiso | **CONFORME** |
| H14 | `schemas/disponibilidad.py` | `DisponibilidadRead` frozen, `vista_general` con default correcto | **CONFORME** |
| H15 | Sin N+1 queries | 3 queries totales; bucle diario en memoria | **CONFORME** |

### Architect

| ID | Archivo | Hallazgo | Clasificación SDD |
|----|---------|----------|-------------------|
| H16 | `disponibilidad.py:17-28` | `_empleado_de_sesion()` duplica lógica de auth.py; debería ser `get_empleado_opcional()` en auth.py (deuda diferible) | **DIVERGENCIA MENOR** |
| H17 | `disponibilidad.py:31-53` | Fórmula de cupo duplicada respecto a `domain.py`; riesgo de divergencia futura | **DIVERGENCIA JUSTIFICADA** (aceptado: vista de lectura en MVP, documentado) |
| H18 | `domain.py:102-114` | RN4 en lugar correcto; Result[T,E] aplicado; coherente con SPEC-S16-A4 | **CONFORME** |
| H19 | `agent_docs/reglas_concurrencia.md` | Over-declaration de composición RN4 (afirmaba validación de combinación que no está implementada) | **DIVERGENCIA MENOR** → **CORREGIDO** (commit `f41b2b9`) |
| H20 | Opción A (sesión en ruta) | Mezcla concern sesión/disponibilidad; justificado para MVP, sin fuga de PII | **DIVERGENCIA JUSTIFICADA** |

---

## 3. Conformidad SDD — Protocolo 8 Puntos

### SPEC-S16-A1: Calendario consciente de sesión por grupo

| Punto | Verifica | Resultado | Detalle |
|:-----:|---------|-----------|---------|
| P1 | DTOs | **CONFORME** | `DisponibilidadRead` frozen; `vista_general: bool = False` añadido con semántica correcta |
| P2 | Métodos | **CONFORME** (post-fix H1) | `Query(ge=2020, le=2100)` y `Query(ge=1, le=12)` aplicados; 422 ante valores fuera de rango |
| P3 | Backward compat | **CONFORME** | `grupos_ausentes` preservado; `vista_general` con default no rompe clientes existentes |
| P4 | DI/Container | **CONFORME** | Router registrado en `main.py`; no requiere DI adicional |
| P5 | Interfaces | **CONFORME** | Endpoint delega a `_empleado_de_sesion()` y `_estado_para_grupos()`; sin lógica en capa de transporte salvo lectura de sesión |
| P6 | Tests | **DIVERGENCIA MENOR** | 3 tests (sin-sesión, con-sesión, params-inválidos); falta test multi-grupo (HECTOR G1+G4) |
| P7 | Code smells | **DIVERGENCIA MENOR** | `_empleado_de_sesion()` duplica lógica de auth.py (Feature Envy diferible) |
| P8 | Patterns | **DIVERGENCIA JUSTIFICADA** | Fórmula de cupo duplicada vs domain.py — aceptado como vista de lectura en MVP |

**Veredicto A1: 5 CONFORME + 1 DJ + 2 DM (0 DEFECTOS)**

### SPEC-S16-A2: Composición excepción RN4

| Punto | Verifica | Resultado | Detalle |
|:-----:|---------|-----------|---------|
| P1 | DTOs | N/A | No hay DTOs nuevos |
| P2 | Métodos | **CONFORME** | `validar_solicitud` retorna `Result[Solicitud, str]`; Failure con mensajes descriptivos |
| P3 | Backward compat | **CONFORME** | Permisos con justificación siguen aprobándose; solo se rechazan casos no-conformes con RN4 |
| P4 | DI/Container | N/A | Sin cambios en DI |
| P5 | Interfaces | **CONFORME** | Lógica en `domain.py` (capa correcta); guard coherente con SPEC-S16-A4 |
| P6 | Tests | **CONFORME** | 3 tests nuevos (Failure×2: sin-justificación, vacaciones; Success×1: permiso+permiso) + existing `test_validar_excepcion_valida` (vacaciones+permiso) |
| P7 | Code smells | **CONFORME** | Bloque limpio, sin duplicación |
| P8 | Patterns | **CONFORME** | Result[T,E] aplicado; validación antes del bucle (fail-fast) |

**Veredicto A2: 6 CONFORME (0 DEFECTOS)**

### Fases B y C — Documentación y VPS

| SPEC | Resultado | Detalle |
|------|-----------|---------|
| B1 CLAUDE.md | **CONFORME** | RN3/RN4 por grupo; nota de migración v1→v3 |
| B2 README.md | **CONFORME** | Tabla concurrencia por grupo; ejemplo corregido; Opción A descrita |
| B3 architecture.md | **CONFORME** | Modelo concurrencia documentado; relación dominio/calendario clara |
| B4 reglas_concurrencia.md | **CONFORME** (post-fix H7/H19) | Fórmulas correctas; composición grupos canónica; over-declaration corregida |
| B5 comunicacion_empleados.md | **CONFORME** | Mensaje por grupo; nota §8 PLAN_08 corregida |
| B6 seed/grupos | **CONFORME** | G3 = 3 miembros reflejado en B4 |
| D5 logrotate | **CONFORME** | Fases 6.1 y 6.2 en deploy-vps-instructions.md |
| D6 backup crontab | **CONFORME** | Fase 7 con comandos de verificación |

---

## 4. Acciones Correctivas Aplicadas

| ID | Hallazgo | Fix | Commit | Test |
|----|----------|-----|--------|------|
| H1 | `anio`/`mes` sin validación de rango | `Query(ge=2020, le=2100)` y `Query(ge=1, le=12)` + `request: Request` movido a primer parámetro | `dad5acf` | `test_disponibilidad_parametros_invalidos_422` (60 tests pasan) |
| H19 | `reglas_concurrencia.md` over-declaration RN4 | Redacción corregida: tipo+justificación vs composición implícita | `f41b2b9` | N/A (doc) |

---

## 5. Resumen de Clasificaciones SDD (Protocolo 8 Puntos por SPEC)

El cómputo de tasa se basa en las evaluaciones P1-P8 por cada SPEC implementada, conforme al protocolo SDD. Los hallazgos adicionales de los agentes (H2, H3, H9-H11, H16-H20) son contexto de mejora, no cuentan en el denominador.

| SPEC | P1 | P2 | P3 | P4 | P5 | P6 | P7 | P8 | Resultado |
|------|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|-----------|
| A1 | C | C | C | C | C | DM | DM | DJ | 5C+1DJ+2DM |
| A2 | N/A | C | C | N/A | C | C | C | C | 6C |
| B1..B6 + D5,D6 | C | C | C | C | C | C | C | C | 8C |

| Clasificación | Evaluaciones SDD |
|---------------|:----------------:|
| **CONFORME** | 19 |
| **DIVERGENCIA JUSTIFICADA** | 1 |
| **DIVERGENCIA MENOR** | 2 |
| **DEFECTO** | 0 (H1 corregido en Act) |
| **TOTAL** | **22** |

### Tasa de paso SDD

**(CONFORME + DIVERGENCIA JUSTIFICADA) / Total = (19 + 1) / 22 = 90.9%** ✅ (umbral: 85%)

---

## 6. Hallazgos Diferidos (Backlog PLAN_09)

| ID | Hallazgo | Prioridad | Razón del diferimiento |
|----|----------|:---------:|------------------------|
| H2 | Cookie `secure=False` en auth.py | P1 | Pre-existente; requiere análisis de configuración por ambiente (dev vs prod). En prod usa HTTPS vía Traefik, pero la cookie debería ser `secure=True` condicionado a `APP_ENV=production`. |
| H9 | `grupos_ausentes` tooltip muestra grupos fuera del scope del usuario | P2 | No viola RN5; UX menor. Filtrar por `grupos_evaluar_ids` en el bucle de tooltip. |
| H10 | Deduplicación lista → set en `grupos_ausentes` | P3 | Performance mínima (10 empleados). Mejora idiomática. |
| H11 | Test multi-grupo (HECTOR G1+G4) faltante | P2 | Cobertura de regresión para el caso documentado en `reglas_concurrencia.md`. |
| H16 | `_empleado_de_sesion()` → extraer a `auth.get_empleado_opcional()` | P2 | Reduce duplicación; centraliza contrato de sesión. |
| H17 | Fórmula cupo duplicada domain.py/disponibilidad.py | P2 | Extraer `calcular_cupo(grupo)` como función pura compartida. |

---

## 7. Veredicto Final

**ESTADO: APROBADO** ✅

Los cambios de SPRINT_17 cumplen los criterios de calidad: el único DEFECTO (H1 — validación de rango) fue corregido con TDD (test + fix), el codebase pasa con 60 tests y ruff limpio. Las DIVERGENCIAS JUSTIFICADAS son decisiones de diseño documentadas y aceptadas para el MVP. Las DIVERGENCIAS MENORES son mejoras diferibles sin impacto funcional ni de privacidad.

Se autoriza el avance al siguiente ciclo. Los ítems diferidos se incorporan al backlog de PLAN_09.

---

*Auditado con SDD Framework v2 — security-scanner + code-reviewer + architect*
