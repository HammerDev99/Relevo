# Workflow SDD — Relevo

Este proyecto sigue el framework **CDAID / SDD** (Spec-Driven Development).

## Ciclo PDCA
1. **Plan**: Se desglosan requerimientos en `docs/plannings/PLAN_NN_*.md`. Cada tarea es un **SPEC**.
2. **Do**: Implementación en `src/`. Se registran avances en `docs/sprints/SPRINT_NN_*.md`.
3. **Check**: Validación técnica (Pytest, Ruff, Mypy) y Auditoría 8 puntos.
4. **Act**: Corrección de defectos críticos en `docs/validate/AUDIT_NN_*.md`.

## Reglas de Oro
- **Ready Check**: No implementar sin SPEC aprobada.
- **Done Check**: No considerar terminado sin tests (Success/Failure) y linter limpio.
- **TDD First**: Escribir el test que falla antes del código que lo resuelve.

## Naming de SPECs
`SPEC-S{sprint}-{fase}{numero}`
Ejemplo: `SPEC-S11-A1` (Sprint 11, Fase A, Item 1).
