# PLAN_06 — Milestone v4 "Mejoras UX, Reglas UI y Gestión de Datos"

| Campo | Valor |
|-------|-------|
| **Fecha** | 2026-05-27 |
| **Fase CDAID** | Plan |
| **Milestone** | v4 |
| **Origen** | Pruebas manuales (Feedback de usuario) |
| **Objetivo** | Mejorar la experiencia de usuario (móvil y automatización de fechas), endurecer las reglas de dominio (evitar duplicidad, límites por solicitud), y habilitar gestión de datos (eliminación en cascada y cambio de claves). |

---

## 1. SPECs de Implementación (Milestone v4)

### SPEC-S14-C1: Gestión de Ciclo de Vida de Datos (Eliminación)
- **Descripción**: Habilitar el borrado seguro de entidades manteniendo la integridad referencial.
- **Criterios de Aceptación**:
    - [ ] **Req 1**: El empleado puede borrar/anular sus propias solicitudes desde la GUI.
    - [ ] **Req 2**: La coordinación puede borrar un usuario de forma definitiva.
    - [ ] El borrado de un usuario elimina en cascada sus solicitudes (`cascade="all, delete-orphan"`) y limpia su relación con los grupos.
- **Estado**: `[ ]`

### SPEC-S14-C2: Reglas Avanzadas de Dominio (Control de Días y Duplicidad)
- **Descripción**: Endurecimiento del motor de validación en `domain.py`.
- **Criterios de Aceptación**:
    - [ ] **Req 4**: El validador bloquea la creación de un permiso si el usuario ya tiene una solicitud (aprobada o pendiente) para ese mismo día.
    - [ ] **Req 7**: Para permisos, se valida que la duración de la solicitud individual no supere los 3 días hábiles (contando fines de semana y festivos con `relevo.festivos`). Continúa aplicando la regla mensual de 3 días máximo en total.
- **Estado**: `[ ]`

### SPEC-S14-C3: Automatización y Experiencia de Usuario (UI/UX)
- **Descripción**: Ajustes en el comportamiento del formulario en `01_solicitudes.py` y optimización visual.
- **Criterios de Aceptación**:
    - [ ] **Req 6**: Si el tipo es `permiso`, al seleccionar la `fecha_inicio`, la `fecha_fin` por defecto debe ser exactamente el mismo día.
    - [ ] **Req 8**: Si el tipo es `vacaciones`, la UI solo solicita la `fecha_inicio`. La `fecha_fin` se calcula automáticamente (22 días calendario) y se muestra en modo solo lectura (o texto) al usuario.
    - [ ] **Req 3**: Inyectar CSS personalizado o reorganizar el layout de columnas (`st.columns`) para apilar los elementos en pantallas pequeñas y mejorar la legibilidad en dispositivos móviles.
- **Estado**: `[ ]`

### SPEC-S14-C4: Seguridad y Perfil de Usuario
- **Descripción**: Permitir que los empleados gestionen sus credenciales.
- **Criterios de Aceptación**:
    - [ ] **Req 5**: Nuevo endpoint PATCH `/usuarios/me/password` en el backend.
    - [ ] Sección de "Mi Perfil" o "Cambiar Contraseña" en la UI (puede ser dentro del portal principal o como una página nueva `04_perfil.py`).
    - [ ] Requiere la contraseña actual para establecer una nueva.
- **Estado**: `[ ]`

---

## 2. Decisiones Arquitectónicas y de Diseño

1. **Cascade Delete vs Soft Delete**: Por instrucción expresa (Req 2 "borrar usuarios y hacer el proceso de limpieza en cascada"), se optará por **Hard Delete** en cascada a nivel de SQLAlchemy (`ondelete="CASCADE"`) para la entidad `Empleado`. Esto requerirá actualizar el modelo.
2. **Mobile UX en Streamlit**: Streamlit es _responsive_ por naturaleza, pero el uso excesivo de `st.columns` fuerza a elementos a encogerse. La solución será utilizar un diseño de una sola columna para formularios o inyectar una regla `@media` CSS para forzar el `flex-direction: column` en las columnas.
3. **Lógica UI (Req 6 y 8)**: Debido a cómo Streamlit maneja el estado (`st.session_state`), las interacciones dinámicas de fecha requerirán usar `on_change` callbacks o recálculo directo en el script top-down para actualizar la UI en tiempo real.

---

**Siguiente paso**: Iniciar `SPRINT_13` para la implementación secuencial de los SPECs definidos, partiendo con las modificaciones de la Base de Datos (S14-C1) y las reglas de Dominio (S14-C2).
