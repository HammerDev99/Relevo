# Arquitectura Relevo — Nivel 2

## Estructura de Capas
1. **Transporte (FastAPI)**: Endpoints REST en `src/app/routes/`.
2. **Esquemas (Pydantic)**: DTOs inmutables en `src/app/schemas/` (Garantizan contrato GUI-API).
3. **Dominio (Business Logic)**: Reglas de negocio puras en `src/app/domain.py` usando `Result[T, E]`.
4. **Persistencia (SQLAlchemy 2.0)**: Modelos en `src/app/models.py`.
5. **Frontend (Streamlit)**: Interfaz modular en `src/app/gui/`.

## Estándar de Comunicación
- La GUI **nunca** accede a la BD directamente.
- Todo intercambio de datos se realiza mediante **DTOs de Pydantic**.
- Los errores de la API se propagan a la GUI mediante el código de estado HTTP y el detalle del error.

## Modelo de Concurrencia por Grupo (v3, autoritativo)

La lógica de concurrencia opera **por grupo**, no globalmente. La fuente autoritativa es `src/app/domain.py::validar_solicitud`.

- **Fórmula**: `cupo_normal = miembros_activos − min_presentes`; excepción: `cupo_normal + 1`.
- Cada grupo valida su cupo independientemente — un ausente en G2 no bloquea a G3.
- `domain.py` itera sobre los grupos del empleado; empleados sin grupos omiten la validación de concurrencia.

### Rol del calendario vs. motor de dominio

| Componente | Responsabilidad |
|-----------|----------------|
| `domain.py::validar_solicitud` | **Fuente autoritativa** — rechaza solicitudes que violan cupo por grupo |
| `routes/disponibilidad.py` | **Vista derivada** — refleja el estado por grupo para cada día del mes |
| `02_disponibilidad.py` (GUI) | Muestra calendario con estado relativo al usuario (con sesión) o general (sin sesión) |

> El calendario es una **proyección** del estado del dominio, no una fuente de verdad. Si hay discrepancia, `domain.py` prevalece.

## Infraestructura Docker
- Hostname `relevo-api`: Servicio de backend (Puerto 8000).
- Hostname `relevo-gui`: Servicio de frontend (Puerto 8501).
- Variable `RELEVO_MODE`: Conmuta el punto de entrada entre API y GUI.
