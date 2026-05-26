import calendar
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Solicitud

router = APIRouter(prefix="/disponibilidad", tags=["disponibilidad"])

@router.get("")
def consultar_disponibilidad(
    anio: int,
    mes: int,
    db: Session = Depends(get_db)
):
    """
    Retorna el estado de disponibilidad por día del mes sin PII (RN5).
    Estados: DISPONIBLE, OCUPADO, EXCEPCIONAL.
    """
    # Rango de fechas del mes
    num_dias = calendar.monthrange(anio, mes)[1]
    fecha_inicio_mes = date(anio, mes, 1)
    fecha_fin_mes = date(anio, mes, num_dias)

    # Obtener todas las solicitudes aprobadas que traslapan con el mes
    query = select(Solicitud).where(
        Solicitud.estado == "aprobada",
        Solicitud.fecha_inicio <= fecha_fin_mes,
        Solicitud.fecha_fin >= fecha_inicio_mes
    )
    solicitudes = db.scalars(query).all()

    resultado: list[dict[str, Any]] = []
    
    for dia in range(1, num_dias + 1):
        actual = date(anio, mes, dia)
        ausentes = [s for s in solicitudes if s.fecha_inicio <= actual <= s.fecha_fin]
        
        count = len(ausentes)
        estado = "DISPONIBLE"
        
        if count >= 2:
            estado = "EXCEPCIONAL"
        elif count == 1:
            # Si hay uno solo, revisamos si es excepción o estándar.
            # Según RN3, el cupo estándar es 1. 
            # Para la vista pública, si hay 1 ausente, el cupo estándar está OCUPADO.
            # Se requiere tramitar como excepción si se quiere ese mismo día.
            estado = "OCUPADO"
            
        resultado.append({
            "fecha": actual.isoformat(),
            "estado": estado
        })
        
    return resultado
