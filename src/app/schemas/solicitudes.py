from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class SolicitudBase(BaseModel):
    tipo: str = Field(..., pattern="^(vacaciones|permiso)$")
    fecha_inicio: date
    fecha_fin: date
    respaldo_id: int
    es_excepcion: bool = False
    justificacion: Optional[str] = None

    model_config = ConfigDict(frozen=True, from_attributes=True)


class SolicitudCreate(SolicitudBase):
    pass


class SolicitudRead(SolicitudBase):
    id: int
    empleado_id: int
    dias_habiles: int
    estado: str
    creada_en: datetime
    procesada_en: Optional[datetime] = None
    procesada_por_id: Optional[int] = None
    
    # Campos adicionales para la GUI (Flattened)
    empleado_nombre: Optional[str] = None
    respaldo_nombre: Optional[str] = None


class SolicitudProcesar(BaseModel):
    nuevo_estado: str = Field(..., pattern="^(aprobada|rechazada)$")

    model_config = ConfigDict(frozen=True)
