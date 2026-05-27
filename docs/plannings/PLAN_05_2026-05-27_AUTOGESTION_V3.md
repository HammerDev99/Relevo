# PLAN_05 — Milestone v3 "Autogestión por Grupos"

| Campo | Valor |
|-------|-------|
| **Fecha** | 2026-05-27 |
| **Fase CDAID** | Plan |
| **Milestone** | v3 |
| **Origen** | Nuevos requerimientos de negocio (Autonomía de oficina) |
| **Objetivo** | Transicionar a un modelo de autogestión con 4 grupos de trabajo, reglas de vacaciones calendario (22 días) y panel de configuración administrativa. |

---

## 1. Definición de Grupos de Trabajo (Modelo de Datos)

| ID | Nombre | Miembros | Min. Presentes |
|----|--------|----------|----------------|
| G1 | Comunicaciones y Atención | Nelly, Hector, Flor | 2 |
| G2 | Fichas EJPMS | Daniel, America, Jackson | 2 |
| G3 | Reparto Const. y Penal | Yesenia, Jorge, Daniela | 2 |
| G4 | Notificaciones y Archivo | Fabian, Hector | 1 (Atípico) |

---

## 2. SPECs de Implementación (Milestone v3)

### SPEC-S13-C1: Re-ingeniería del Motor de Grupos
- **Descripción**: Actualizar `models.py` para soportar Grupos (M:N para Hector) y reescribir `domain.py`.
- **Criterios de Aceptación**:
    - [x] `Empleado` tiene relación con `Grupo`.
    - [x] Validador detecta si la ausencia baja el cupo del grupo según su `min_presentes`.
    - [x] Hector afecta la concurrencia de G1 y G4 simultáneamente.
- **Estado**: `[x]`

### SPEC-S13-C2: Lógica de Vacaciones y Calendario "Sunday-First"
- **Descripción**: Modificar la GUI y el motor `relevo` para la nueva cuenta de días.
- **Criterios de Aceptación**:
    - [x] Al elegir `tipo='vacaciones'`, el sistema proyecta 22 días calendario (sin saltar festivos).
    - [x] El componente de calendario en Streamlit inicia la semana en Domingo.
    - [x] Los permisos (hasta 3/mes) siguen permitiendo fraccionamiento o días seguidos.
- **Estado**: `[x]`

### SPEC-S13-C3: Sistema de Alertas y Autogestión (Save with Exception)
- **Descripción**: Eliminar flujo de aprobación. El sistema avisa pero no bloquea.
- **Criterios de Aceptación**:
    - [x] Si `validar_solicitud` devuelve error de concurrencia, la GUI muestra advertencia de "Trámite Excepcional".
    - [x] El botón de guardar permite confirmar la excepción sin aprobación previa.
    - [x] El relevo (backup) se filtra automáticamente por miembros del mismo grupo.
- **Estado**: `[x]`

### SPEC-S13-C4: Panel de Configuración (Admin CRUD)
- **Descripción**: Nueva vista para el rol `coordinacion` para gestionar el sistema.
- **Criterios de Aceptación**:
    - [x] CRUD de Usuarios (Gestionar personal).
    - [x] Gestión de Grupos (Asignar miembros).
    - [x] Parámetros Globales (Editar `min_presentes` o `dias_vacaciones`).
- **Estado**: `[x]`

---

## 3. Protocolo de Transición (Checklist v2)

1. **DB Migration**: Añadir tablas `grupos` y `empleado_grupo`.
2. **Domain Update**: El motor de reglas ahora es "Group-Aware".
3. **GUI Pivot**: Renombrar "Aprobaciones" a "Configuración/Log".
4. **Test Regression**: Asegurar que las reglas de festivos colombianos sigan vigentes para los calendarios visuales.

---

**Siguiente paso**: SPRINT_12 completado y auditado (AUDIT_06_2026-05-27_GATE_F3_AUTOGESTION.md). Milestone v3 listo para integración final.
