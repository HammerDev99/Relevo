from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Form, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import get_coordinador
from app.database import get_db
from app.models import Empleado, Solicitud
from app.schemas.solicitudes import SolicitudRead

router = APIRouter(prefix="/coordinacion", tags=["coordinacion"])

@router.get("/solicitudes/pendientes", response_model=list[SolicitudRead])
def listar_pendientes(
    db: Session = Depends(get_db),
    admin: Empleado = Depends(get_coordinador)
) -> list[SolicitudRead]:
    """Lista todas las solicitudes pendientes de todos los empleados (Solo Admin)."""
    query = select(Solicitud).where(Solicitud.estado == "pendiente")
    solicitudes = db.scalars(query).all()
    
    # Enriquecer con datos del empleado (PII permitida para coordinación)
    resultado = []
    for s in solicitudes:
        s_dict = SolicitudRead.model_validate(s)
        resultado.append(s_dict.model_copy(update={
            "empleado_nombre": s.empleado.nombre,
            "respaldo_nombre": s.respaldo.nombre if s.respaldo else "N/A"
        }))
    return resultado

@router.post("/solicitudes/{solicitud_id}/procesar")
def procesar_solicitud(
    solicitud_id: int,
    nuevo_estado: str = Form(...), # 'aprobada' o 'rechazada'
    db: Session = Depends(get_db),
    admin: Empleado = Depends(get_coordinador)
) -> dict[str, str]:
    """Aprueba o rechaza una solicitud (Solo Admin)."""
    solicitud = db.get(Solicitud, solicitud_id)
    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    
    if nuevo_estado not in ["aprobada", "rechazada"]:
        raise HTTPException(status_code=400, detail="Estado inválido")
        
    solicitud.estado = nuevo_estado
    solicitud.procesada_en = datetime.now(UTC)
    solicitud.procesada_por_id = admin.id
    
    db.commit()
    return {"message": f"Solicitud {nuevo_estado} exitosamente"}
