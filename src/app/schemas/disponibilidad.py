from datetime import date

from pydantic import BaseModel, ConfigDict


class DisponibilidadRead(BaseModel):
    fecha: date
    estado: str # 'DISPONIBLE', 'OCUPADO', 'EXCEPCIONAL', 'FESTIVO'
    razon: str | None = None

    model_config = ConfigDict(frozen=True, from_attributes=True)
