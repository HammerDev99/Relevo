from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Form, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import get_coordinador
from ..database import get_db
from ..models import Empleado, Solicitud

router = APIRouter(prefix="/coordinacion", tags=["coordinacion"])

@router.get("/solicitudes/pendientes")
def listar_pendientes(
    db: Session = Depends(get_db),
    admin: Empleado = Depends(get_coordinador)
):
    """Lista todas las solicitudes pendientes de todos los empleados (Solo Admin)."""
    query = select(Solicitud).where(Solicitud.estado == "pendiente")
    solicitudes = db.scalars(query).all()
    
    # Enriquecer con datos del empleado (PII permitida para coordinación)
    resultado = []
    for s in solicitudes:
        emp = db.get(Empleado, s.empleado_id)
        respaldo = db.get(Empleado, s.respaldo_id) if s.respaldo_id else None
        
        resultado.append({
            "id": s.id,
            "empleado_nombre": emp.nombre if emp else "Desconocido",
            "tipo": s.tipo,
            "fecha_inicio": s.fecha_inicio,
            "fecha_fin": s.fecha_fin,
            "dias_habiles": s.dias_habiles,
            "respaldo_nombre": respaldo.nombre if respaldo else "N/A",
            "es_excepcion": s.es_excepcion,
            "justificacion": s.justificacion,
            "creada_en": s.creada_en
        })
    return resultado

@router.post("/solicitudes/{solicitud_id}/procesar")
def procesar_solicitud(
    solicitud_id: int,
    nuevo_estado: str = Form(...), # 'aprobada' o 'rechazada'
    db: Session = Depends(get_db),
    admin: Empleado = Depends(get_coordinador)
):
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
