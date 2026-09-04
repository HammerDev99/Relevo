from datetime import date

from pydantic import BaseModel, ConfigDict


class DisponibilidadRead(BaseModel):
    fecha: date
    estado: str  # 'DISPONIBLE', 'OCUPADO', 'EXCEPCIONAL'
    razon: str | None = None
    grupos_ausentes: list[str] = []  # SPEC-S15-C5: nombres de grupos
    vista_general: bool = False  # SPEC-S16-A1: True = sin sesión o sin grupos
    # SPEC-S18-A1 (RN5, PLAN_09): nombres de ausentes.
    # Solo se puebla con sesión válida; nunca incluye tipo ni justificación.
    empleados_ausentes: list[str] = []

    model_config = ConfigDict(frozen=True, from_attributes=True)
