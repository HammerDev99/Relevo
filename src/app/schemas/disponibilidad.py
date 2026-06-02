from datetime import date

from pydantic import BaseModel, ConfigDict


class DisponibilidadRead(BaseModel):
    fecha: date
    estado: str  # 'DISPONIBLE', 'OCUPADO', 'EXCEPCIONAL'
    razon: str | None = None
    grupos_ausentes: list[str] = []  # SPEC-S15-C5: nombres de grupos (sin PII)
    vista_general: bool = False  # SPEC-S16-A1: True = sin sesión o sin grupos

    model_config = ConfigDict(frozen=True, from_attributes=True)
