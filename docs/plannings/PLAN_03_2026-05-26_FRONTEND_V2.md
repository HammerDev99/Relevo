# PLAN_03 — Frontend v2 "Relevo" (Streamlit + FastAPI)

| Campo | Valor |
|-------|-------|
| **Fecha** | 2026-05-26 |
| **Fase CDAID** | Plan |
| **Milestone** | v2 |
| **Origen** | PLAN_02 §8.5 (Cierre v1) |
| **Objetivo** | Implementar una interfaz de usuario profesional y reactiva utilizando Streamlit, siguiendo los estándares de diseño y estructura de Sherlock-docs. |

## 1. Arquitectura Propuesta (Alineada con Sherlock-docs)

Basado en la referencia de `sherlock-docs`, el frontend de Relevo se estructurará de forma modular para garantizar escalabilidad y mantenimiento:

```
src/app/gui/
├── app.py              # Punto de entrada (Configuración, Sidebar, Routing)
├── session_keys.py      # Constantes para st.session_state
├── utils.py             # Helpers de UI (formateo, iconos)
├── components/          # Componentes reutilizables (Calendario, Tablas)
├── services/            # Clientes de API (AuthService, RequestService)
└── pages/               # Vistas principales
    ├── 01_solicitudes.py     # Mis Solicitudes y Nueva Solicitud
    ├── 02_disponibilidad.py # Calendario público (RN5)
    └── 03_coordinacion.py   # Panel de control (Solo Coordinadores)
```

## 2. Flujo de Autenticación Integrado

- Streamlit manejará su propia persistencia en `st.session_state`.
- Se implementará un `AuthService` que sincronice las credenciales con los endpoints `/login` de FastAPI.
- El rol del usuario (`empleado` vs `coordinacion`) determinará la visibilidad de las páginas en el sidebar.

## 3. SPECs Verificables (Sprint 07-09)

### SPEC-V2-F1: Infraestructura y Auth GUI
- [x] Estructura de carpetas y archivos base.
- [x] Implementación de `services/auth_service.py` (cliente HTTP).
- [x] Pantalla de Login con manejo de errores (401).

### SPEC-V2-F2: Portal del Empleado (Solicitudes)
- [ ] Vista de "Mis Solicitudes" (Lista/Cards).
- [ ] Formulario de "Nueva Solicitud" interactivo (Date pickers + dropdown de compañeros).
- [ ] Integración con `validar_solicitud` (mostrar errores de cupo en la UI).

### SPEC-V2-F3: Calendario de Disponibilidad (RN5)
- [ ] Visualización gráfica del calendario mensual.
- [ ] Colores por estado (Verde: Libre, Naranja: Ocupado, Rojo: Excepcional).
- [ ] Garantizar anonimato absoluto (PII Shield).

### SPEC-V2-F4: Panel de Coordinación (Admin)
- [ ] Lista de solicitudes pendientes de aprobación.
- [ ] Detalle de solicitud (incluye PII: nombre, motivo, justificación).
- [ ] Acciones: Aprobar / Rechazar (Actualiza `estado` en BD).

### SPEC-V2-F5: Dockerización Unificada
- [ ] Actualizar `Dockerfile` y `entrypoint.sh` para soportar `RELEVO_MODE=gui|api`.
- [ ] Configurar `HEALTHCHECK` para ambos servicios.

---

## 4. Preguntas para Refinar el Contexto

Para alinear el desarrollo al 100% con tu visión profesional, por favor responde:

1. **Estrategia de Despliegue**: ¿Prefieres un **contenedor único** que corra ambos servicios (FastAPI y Streamlit) usando procesos separados, o **dos contenedores independientes** en el mismo `docker-compose`? (Sherlock usa el modo por variable de entorno).
2. **Consumo de Lógica**: ¿Debe Streamlit llamar a la API vía **HTTP (REST)** o prefieres que importe directamente los módulos de `src/app/domain.py` y `database.py`? (Sherlock parece ser modular pero independiente).
3. **Estética**: ¿Hay algún tema de Streamlit (colores, fuentes) o librería de componentes (ej. `streamlit-extras`, `streamlit-antd-components`) que se use en Sherlock y que debamos replicar aquí?
4. **Persistencia de Sesión**: ¿Deseas usar una configuración tipo `auth_config.yaml` externa para usuarios estáticos o nos mantenemos exclusivamente con la tabla `empleados` de la BD?
