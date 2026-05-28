# SPRINT_14 — Mejoras de Calendario, UX y Seguridad

**Fecha inicio**: 2026-05-27
**Objetivo**: Implementar mejoras de calendario (inicio domingo, tooltips, interactividad), corregir problemas de renderizado móvil, validar reglas combinadas de vacaciones/permisos, y completar funcionalidad de gestión de perfil de usuario.
**Planning**: `docs/plannings/PLAN_07_2026-05-27_MEJORAS_CALIFICACION_UX.md`
**Metodología**: SDD / CDAID v2

## Estado General

SPRINT_14: [██████████████░░░] 85% (7/8 SPECs activos) - AUDITADO (AUDIT_08)

| Fase | Total | Completados | Diferidos |
|------|:-----:|:-----------:|:----------:|
| A (Backend) | 3 | 3 | 0 |
| B (Frontend Calendario) | 4 | 2 | 2 |
| C (Frontend Móvil) | 3 | 2 | 1 |

## Registro de Progreso

| Fecha | SPEC | Descripción | Commit | Tests |
|-------|------|-------------|--------|:-----:|
| 2026-05-27 | SPEC-S15-C1 | Test regla combinada vacaciones+permisos mismo mes | 53b77d1 | +1 |
| 2026-05-27 | SPEC-S14-C4 | Endpoint PATCH /usuarios/me/password | cc445e8 | +4 |
| 2026-05-27 | SPEC-S14-C4 | UI Perfil (04_perfil.py) | cb90e17 | 0 |
| 2026-05-27 | SPEC-S15-C2 | Calendario inicio Domingo | b08305e | 0 |
| 2026-05-27 | SPEC-S15-C4 | No pintar no-hábiles en permisos | 440adce | +2 |
| 2026-05-27 | SPEC-S15-C3 | Justificación opcional (backend + UI) | 1e6606b | +1 |
| 2026-05-27 | SPEC-S15-C7 | Corrección móvil V2 (CSS responsivo) | 8277758 | 0 |

## SPECs Diferidos (Alta Complejidad)

| ID | Descripción | Razón |
|----|-------------|-------|
| SPEC-S15-C5 | Tooltip de grupos | Streamlit no soporta tooltips nativos - requiere HTML/CSS custom |
| SPEC-S15-C6 | Calendario interactivo | Requiere implementación custom con session_state |

## Métricas de Verificación

| Métrica | Pre-Sprint | Post-Sprint | Delta |
|---------:|:----------:|:-----------:|:-----:|
| Tests | 46 | 54 | +8 |
| Coverage | ~80% | ~84% | +4% |
| Ruff errors | 0 | 0 | 0 |

## Decisiones Tomadas

| # | Decisión | Razón | Alt. descartada |
|---|----------|-------|-----------------|
| 1 | Diferir SPEC-S15-C5 y C6 a PLAN_08 | Alta complejidad técnica con Streamlit | Implementar ahora con soluciones subóptimas |
| 2 | Completar SPEC-S15-C7 con CSS responsivo | Solución viable siguiendo mejores prácticas Streamlit | Implementación custom compleja |

## Trazas de Delegación

| Decisión | Propuesta IA | Aprobación Humano |
|----------|-------------|-------------------|
| Diferir tooltips e interactividad | Sugerir diferir por complejidad | Aprobado |
| Completar corrección móvil con CSS | Aplicar media queries y responsive design | Aprobado |
