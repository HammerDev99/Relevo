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

## Infraestructura Docker
- Hostname `relevo-api`: Servicio de backend (Puerto 8000).
- Hostname `relevo-gui`: Servicio de frontend (Puerto 8501).
- Variable `RELEVO_MODE`: Conmuta el punto de entrada entre API y GUI.
