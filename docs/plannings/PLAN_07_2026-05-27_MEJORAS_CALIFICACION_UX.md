# PLAN_07 — Milestone v5 "Mejoras de Calendario, UX y Seguridad"

| Campo | Valor |
|-------|-------|
| **Fecha** | 2026-05-27 |
| **Fase CDAID** | Plan |
| **Milestone** | v5 |
| **Origen** | Pruebas manuales (Feedback de usuario) + SPEC pendiente PLAN_06 |
| **Objetivo** | Mejorar la experiencia de usuario en calendario (visualización e interactividad), corregir problemas de renderizado móvil, validar reglas combinadas de vacaciones/permisos, y completar la funcionalidad de gestión de perfil de usuario. |

---

## 1. Estado Previo / Contexto

| Metrica | Valor actual | Target |
|---------:|:-----------:|:------:|
| Tests | 13 archivos tests | +3 nuevos |
| Coverage | ~80% | ~85% |
| Sprints completados | 13 | 14 |
| Milestone actual | v4 (parcial) | v5 |

**Contexto**: El PLAN_06 dejó pendiente SPEC-S14-C4 (Seguridad y Perfil de Usuario) y se identificaron 7 nuevos requerimientos durante pruebas manuales que se formalizan en este planning.

---

## 2. SPECs de Implementación (Milestone v5)

### SPEC-S14-C4: Seguridad y Perfil de Usuario (Pendiente PLAN_06)
- **Descripción**: Permitir que los empleados gestionen sus credenciales.
- **Criterios de Aceptación**:
    - [x] **Req 5**: Nuevo endpoint PATCH `/usuarios/me/password` en el backend.
    - [x] Sección de "Mi Perfil" o "Cambiar Contraseña" en la UI (página nueva `04_perfil.py`).
    - [x] Requiere la contraseña actual para establecer una nueva.
- **Estado**: `[x]`
- **Prioridad**: P1
- **Verificado**: 2026-05-27 | **Commits**: cc445e8 (endpoint), cb90e17 (UI)

### SPEC-S15-C1: Regla Combinada Vacaciones+Permisos
- **Descripción**: Confirmar que es posible pedir vacaciones y permisos (hasta 3 días) en el mismo mes.
- **Criterios de Aceptación**:
    - [x] Test específico que valide que un empleado puede solicitar vacaciones y permisos en el mismo mes sin conflicto.
    - [x] Verificar que el motor de reglas maneja independientemente el saldo anual de vacaciones y el mensual de permisos.
- **Estado**: `[x]`
- **Prioridad**: P1
- **Verificado**: 2026-05-27 | **Commit**: 53b77d1

### SPEC-S15-C2: UX Calendario (Inicio en Domingo)
- **Descripción**: Configurar el calendario para que inicie en Domingo en la GUI de Disponibilidad.
- **Criterios de Aceptación**:
    - [x] El calendario en `02_disponibilidad.py` muestra los días comenzando por Domingo.
    - [x] Consistencia visual con calendarios estándar en Colombia.
- **Estado**: `[x]`
- **Prioridad**: P2
- **Verificado**: 2026-05-27 | **Commit**: b08305e

### SPEC-S15-C3: UI Flexible (Justificación Opcional)
- **Descripción**: Hacer que el campo de "Justificación/Motivo" sea opcional para todos los tipos de solicitud.
- **Criterios de Aceptación**:
    - [x] Eliminar la restricción de campo obligatorio en el formulario de `01_solicitudes.py`.
    - [x] Validar que el backend acepta solicitudes sin motivo.
- **Estado**: `[x]`
- **Prioridad**: P2
- **Verificado**: 2026-05-27 | **Commit**: 1e6606b

### SPEC-S15-C4: Visualización Selectiva (No pintar no-hábiles)
- **Descripción**: En la vista de disponibilidad, no pintar festivos ni fines de semana para los rangos de permisos.
- **Criterios de Aceptación**:
    - [x] El calendario en `02_disponibilidad.py` omite colorear festivos y fines de semana en permisos.
    - [x] Limpieza visual para mejorar legibilidad.
- **Estado**: `[x]`
- **Prioridad**: P2
- **Verificado**: 2026-05-27 | **Commit**: 440adce

### SPEC-S15-C5: Tooltip de Grupos
- **Descripción**: Mostrar hover con los nombres de los grupos que ocupan una fecha. Activación gestionable por Coordinación.
- **Criterios de Aceptación**:
    - [ ] Implementar tooltip al pasar el mouse sobre fechas ocupadas en `02_disponibilidad.py`.
    - [ ] Mostrar nombres de grupos que tienen ausencias en esa fecha.
    - [ ] Configuración en panel de coordinación para activar/desactivar tooltips.
- **Estado**: `[ ]`
- **Prioridad**: P1

### SPEC-S15-C6: Calendario Interactivo
- **Descripción**: Permitir clic en fecha para ver alerta de ocupación o redirigir a creación con fecha pre-cargada.
- **Criterios de Aceptación**:
    - [ ] Implementar interactividad al hacer clic en fechas del calendario en `02_disponibilidad.py`.
    - [ ] Mostrar alerta con información de ocupación o redirigir a formulario de solicitud con fecha pre-cargada.
- **Estado**: `[ ]`
- **Prioridad**: P1

### SPEC-S15-C7: Optimización Móvil V2
- **Descripción**: Corregir problemas de renderizado detectados en dispositivos móviles (Ref: Screenshot 151919).
- **Criterios de Aceptación**:
    - [x] Revisar y corregir el renderizado específico en dispositivos móviles.
    - [x] Ajustar CSS/layout para mejorar legibilidad en pantallas pequeñas.
    - [x] Validar en múltiples tamaños de pantalla móvil (media queries).
- **Estado**: `[x]`
- **Prioridad**: P0
- **Verificado**: 2026-05-27 | **Commit**: 8277758

---

## 3. Decisiones Arquitectónicas y de Diseño

1. **Estructura por Capa Técnica**: 
   - **Fase A (Backend)**: SPEC-S14-C4 (endpoint password) + SPEC-S15-C1 (validación reglas)
   - **Fase B (Frontend Calendario)**: SPEC-S15-C2, C4, C5, C6 (mejoras visuales e interactividad)
   - **Fase C (Frontend Móvil)**: SPEC-S15-C3, C7 (flexibilidad y corrección móvil)

2. **Tooltip en Streamlit**: Streamlit no soporta tooltips nativos. Se implementará usando `st.tooltip` (si disponible) o mediante HTML personalizado con `st.markdown` y CSS.

3. **Interactividad Calendario**: Streamlit maneja el estado de forma top-down. Para interactividad se usará `st.session_state` para almacenar la fecha seleccionada y redirigir al formulario.

4. **Justificación Opcional**: Se modificará el esquema de validación en `schemas/solicitudes.py` para hacer el campo `motivo` opcional (`Optional[str]`).

5. **Calendario Domingo**: Streamlit's `st.date_input` no permite configurar el día de inicio. Se usará una implementación personalizada o se migrará a un componente de calendario más flexible.

---

## 4. Alcance por Fases

### Fase A — Backend (Reglas y Seguridad)

| ID | Hallazgo | Archivo(s) | Fix propuesto | Esfuerzo |
|----|----------|-----------|---------------|:--------:|
| A-01 | SPEC-S14-C4: Endpoint password | `src/app/routes/auth.py` | Agregar PATCH `/usuarios/me/password` | Medio |
| A-02 | SPEC-S14-C4: UI Perfil | `src/app/gui/pages/04_perfil.py` (nuevo) | Crear página de perfil con cambio de clave | Medio |
| A-03 | SPEC-S15-C1: Test regla combinada | `tests/v1/test_domain.py` | Test vacaciones+permisos mismo mes | Bajo |

### Fase B — Frontend Calendario

| ID | Hallazgo | Archivo(s) | Fix propuesto | Esfuerzo |
|----|----------|-----------|---------------|:--------:|
| B-01 | SPEC-S15-C2: Calendario Domingo | `src/app/gui/pages/02_disponibilidad.py` | Configurar inicio en Domingo | Medio |
| B-02 | SPEC-S15-C4: No pintar no-hábiles | `src/app/gui/pages/02_disponibilidad.py` | Filtrar festivos/fines de semana en render | Medio |
| B-03 | SPEC-S15-C5: Tooltip grupos | `src/app/gui/pages/02_disponibilidad.py` | Implementar hover con info grupos | Alto |
| B-04 | SPEC-S15-C6: Calendario interactivo | `src/app/gui/pages/02_disponibilidad.py` | Clic → alerta o redirección | Alto |

### Fase C — Frontend Móvil

| ID | Hallazgo | Archivo(s) | Fix propuesto | Esfuerzo |
|----|----------|-----------|---------------|:--------:|
| C-01 | SPEC-S15-C3: Justificación opcional | `src/app/schemas/solicitudes.py` | Hacer campo `motivo` opcional | Bajo |
| C-02 | SPEC-S15-C3: UI opcional | `src/app/gui/pages/01_solicitudes.py` | Eliminar validación de required | Bajo |
| C-03 | SPEC-S15-C7: Corrección móvil | `src/app/gui/pages/*.py` | Ajustar CSS/layout para móvil | Alto |

---

## 5. Esfuerzo Total

| Fase | Items | Esfuerzo estimado |
|------|:-----:|:-----------------:|
| A (Backend) | 3 | 4 horas |
| B (Frontend Calendario) | 4 | 8 horas |
| C (Frontend Móvil) | 3 | 6 horas |
| **Total** | **10** | **18 horas** |

---

## 6. Criterios de Éxito

- [x] Items Fase A implementados y tests pasando
- [x] Items Fase B (parcial) implementados con validación visual
- [x] Items Fase C (parcial) implementados
- [x] `pytest -x` pasa sin regresión
- [x] `ruff check src/` limpio
- [x] Tests nuevos: +8 (excede mínimo de +3)
- [x] Auditoría SDD post-implementación con tasa ≥85% (AUDIT_08)

---

## 7. Hallazgos Diferidos

| ID | Hallazgo | Razon |
|----|----------|-------|
| SPEC-S15-C5 | Tooltip de grupos | Alta complejidad técnica (Streamlit no soporta tooltips nativos) - Diferido a PLAN_08 |
| SPEC-S15-C6 | Calendario interactivo | Alta complejidad técnica (requiere implementación custom) - Diferido a PLAN_08 |

---

## 8. Dependencias y Riesgos

| Riesgo | Impacto | Mitigación |
|--------|:-------:|------------|
| Streamlit no soporta tooltips nativos | Medio | Implementar con HTML/CSS personalizado |
| Calendario inicio Domingo no configurable en Streamlit | Alto | Usar componente personalizado o librería externa |
| Renderizado móvil variable por dispositivo | Medio | Validar en múltiples dispositivos/resoluciones |
| Validación password requiere re-autenticación | Bajo | Usar sesión actual para verificar password actual |

---

**Nota**: Este planning integra el SPEC pendiente del PLAN_06 (SPEC-S14-C4) y los 7 nuevos requerimientos identificados en pruebas manuales, organizados por capa técnica para facilitar la implementación y verificación.
