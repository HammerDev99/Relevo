# PLAN_04 — Consolidación y Milestone v3 "Relevo"

| Campo | Valor |
|-------|-------|
| **Fecha** | 2026-05-26 |
| **Fase CDAID** | Plan |
| **Milestone** | v3 |
| **Origen** | AUDIT_05 (Deuda técnica) + Feedback de pruebas manuales |
| **Objetivo** | Resolver deuda técnica crítica (Logging, DTOs), corregir errores de infraestructura detectados en pruebas y desarrollar funciones avanzadas de gestión. |

## 1. Fase A: Deuda Técnica y Robustez (Prioridad Alta)

No se avanzará a nuevas funcionalidades sin cerrar estos puntos detectados en la auditoría experta AUDIT_05.

### SPEC-S11-A1: Logging Unificado GUI
- **Origen**: AUDIT_05 §1.
- **Objetivo**: Implementar trazabilidad total en la capa Streamlit.
- **Cambios**: Crear `src/app/gui/utils/logger.py` y decorar servicios para registrar cada petición/error hacia la API.
- **Criterio**: Logs visibles en `docker logs relevo-gui` con contexto de usuario y error.
- **Estado**: `[x]` Completado

### SPEC-S11-A2: DTOs Inmutables (Pydantic v2)
- **Origen**: AUDIT_05 §1.
- **Objetivo**: Eliminar el transporte vía diccionarios genéricos.
- **Cambios**: Crear `src/app/schemas/` con modelos Pydantic inmutables para Solicitudes, Usuarios y Disponibilidad.
- **Criterio**: Tipado estricto en la API y validación inmediata en los servicios de la GUI.
- **Estado**: `[x]` Completado

## 2. Fase B: Correcciones de Pruebas Manuales (Act)

### SPEC-S12-B1: Fix Crítico de Imports en Docker
- **Defecto**: `ModuleNotFoundError: No module named 'app.gui'`.
- **Análisis**: Conflicto de resolución de paquetes en el entorno contenedorizado.
- **Cambio**: Aplanar estructura de imports o corregir `PYTHONPATH` y `__init__.py` para asegurar que el modo `gui` sea tan estable como el modo `api`.
- **Estado**: `[x]` Completado (Normalización a absolute imports app.* / relevo.*)

## 3. Fase C: Milestone v3 - Gestión Avanzada

Refinado según requerimientos de valor para coordinación:

### SPEC-S13-C1: Reporte Visual de Ausencias (Heatmap/Timeline)
- **Coordinación**: Vista de equipo que permite ver solapamientos y ausencias de un vistazo.
- **Empleados**: Visualización interactiva de días consumidos vs. disponibles.

### SPEC-S13-C2: Dashboard de Riesgo Operativo
- **Objetivo**: Alertas automáticas cuando la cantidad de empleados disponibles caiga por debajo del umbral de seguridad para una fecha.
- **Indicador**: Semáforo de riesgo por día en el calendario de coordinación.

### SPEC-S13-C3: Exportación MVP (CSV/Excel)
- **Objetivo**: Descarga de datos para reportes externos a la Rama Judicial.

---

## 4. Resumen de Sprints (v3)

| Sprint | Enfoque | SPECs | Estado |
|--------|---------|-------|--------|
| SPRINT_11 | Deuda Técnica & Fixes | S11-A1, S11-A2, S12-B1 | Pendiente |
| SPRINT_12 | Reportes Visuales | S13-C1 | Pendiente |
| SPRINT_13 | Gestión de Riesgo | S13-C2, S13-C3 | Pendiente |
