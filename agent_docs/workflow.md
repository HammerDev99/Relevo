# Workflow SDD — Relevo (CDAID Framework v2)

Este proyecto sigue el framework **CDAID v2 / SDD** (Contract-Driven Artificial Intelligence Development - Spec-Driven Development).

## Ciclo PDCA (4 Fases)

1. **Plan** (`docs/plannings/`): Desglose de requerimientos en SPECs con criterios verificables. Decisiones arquitectónicas, riesgos y esfuerzo estimado.
2. **Do** (`docs/sprints/`): Implementación con SPECs como contrato. TDD, quality gates, tracking de progreso.
3. **Check** (`docs/validate/`): Verificación mediante tests, análisis estático, auditoría multi-agente (8 puntos SDD). Un archivo `AUDIT_NN_*.md` por auditoría.
4. **Act** (Correcciones en `AUDIT_*.md`): Corrección de hallazgos CRITICAL/HIGH con TDD. Hallazgos MEDIUM diferidos → siguiente Planning.

## Reglas de Oro
- **Ready Check**: No implementar sin SPEC aprobada.
- **Done Check**: No considerar terminado sin tests (Success/Failure) y linter limpio.
- **TDD First**: Escribir el test que falla antes del código que lo resuelve.
- **Quality Gate**: Todo cambio pasa `pytest -x` + `ruff check` + auditoría SDD (tasa ≥85%).

## Naming de SPECs
`SPEC-S{sprint}-{fase}{numero}`
Ejemplo: `SPEC-S15-A1` (Sprint 15, Fase A, Item 1).

## Naming de Auditorías
`AUDIT_{NN}_{YYYY-MM-DD}_{SLUG}.md`
Ejemplo: `AUDIT_08_2026-05-27_GATE_F5_CALIFICACION_UX.md`

## Protocolo SDD (8 Puntos)
| Punto | Verifica |
|-------|----------|
| P1 | DTOs — frozen, campos, JSON serializable |
| P2 | Metodos — firma, Result[T,E], paths Success/Failure |
| P3 | Backward compat — callers no rotos |
| P4 | DI/Container — registrado correctamente |
| P5 | Interfaces — delegan correctamente |
| P6 | Tests — Success, Failure, cantidad, coverage |
| P7 | Code smells — Feature Envy, Duplicate Code eliminados |
| P8 | Patterns — Facade, DI, ROP implementados |

**Tasa de aprobación**: (CONFORME + JUSTIFICADA) / Total ≥ 85%
