from datetime import date

from fastapi import APIRouter, Depends, Form, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import get_empleado_actual
from app.database import get_db
from app.domain import validar_solicitud
from app.models import Empleado, Solicitud
from app.schemas.solicitudes import SolicitudRead
from relevo.result import Failure

router = APIRouter(prefix="/solicitudes", tags=["solicitudes"])

@router.get("", response_model=list[SolicitudRead])
def listar_solicitudes(
    db: Session = Depends(get_db),
    empleado: Empleado = Depends(get_empleado_actual)
) -> list[SolicitudRead]:
    """Retorna las solicitudes del empleado autenticado."""
    query = select(Solicitud).where(Solicitud.empleado_id == empleado.id)
    solicitudes = db.scalars(query).all()
    
    # Mapeo manual para incluir nombres si es necesario (o confiar en relationship + property)
    res = []
    for s in solicitudes:
        s_dict = SolicitudRead.model_validate(s)
        # Asegurar nombres para la GUI
        res.append(s_dict.model_copy(update={
            "empleado_nombre": s.empleado.nombre,
            "respaldo_nombre": s.respaldo.nombre if s.respaldo else "N/A"
        }))
    return res

@router.post("/nueva", response_model=SolicitudRead)
def crear_solicitud(
    tipo: str = Form(...),
    fecha_inicio: date = Form(...),
    fecha_fin: date = Form(...),
    respaldo_id: int = Form(...),
    es_excepcion: bool = Form(False),
    justificacion: str | None = Form(None),
    db: Session = Depends(get_db),
    empleado: Empleado = Depends(get_empleado_actual)
) -> SolicitudRead:
    """Crea una nueva solicitud previa validación de dominio."""
    nueva = Solicitud(
        empleado_id=empleado.id,
        tipo=tipo,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        respaldo_id=respaldo_id,
        es_excepcion=es_excepcion,
        justificacion=justificacion,
        estado="aprobada" # S13-C3: Autogestión
    )

    # Validar contra reglas de negocio
    resultado = validar_solicitud(db, nueva)
    if isinstance(resultado, Failure):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=resultado.error
        )

    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    
    res = SolicitudRead.model_validate(nueva)
    return res.model_copy(update={
        "empleado_nombre": empleado.nombre,
        "respaldo_nombre": nueva.respaldo.nombre if nueva.respaldo else "N/A"
    })

@router.delete("/{solicitud_id}")
def eliminar_solicitud(
    solicitud_id: int,
    db: Session = Depends(get_db),
    empleado: Empleado = Depends(get_empleado_actual)
) -> dict[str, str]:
    """Elimina o anula una solicitud propia."""
    solicitud = db.get(Solicitud, solicitud_id)
    if not solicitud or solicitud.empleado_id != empleado.id:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    
    db.delete(solicitud)
    db.commit()
    return {"message": "Solicitud eliminada exitosamente"}
