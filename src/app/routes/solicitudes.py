from datetime import date

from fastapi import APIRouter, Depends, Form, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import get_empleado_actual
from ..database import get_db
from ..domain import validar_solicitud
from ..models import Empleado, Solicitud

router = APIRouter(prefix="/solicitudes", tags=["solicitudes"])

@router.get("")
def listar_solicitudes(
    db: Session = Depends(get_db),
    empleado: Empleado = Depends(get_empleado_actual)
):
    """Retorna las solicitudes del empleado autenticado."""
    query = select(Solicitud).where(Solicitud.empleado_id == empleado.id)
    return db.scalars(query).all()

@router.post("/nueva")
def crear_solicitud(
    tipo: str = Form(...),
    fecha_inicio: date = Form(...),
    fecha_fin: date = Form(...),
    respaldo_id: int = Form(...),
    es_excepcion: bool = Form(False),
    justificacion: str | None = Form(None),
    db: Session = Depends(get_db),
    empleado: Empleado = Depends(get_empleado_actual)
):
    """Crea una nueva solicitud previa validación de dominio."""
    nueva = Solicitud(
        empleado_id=empleado.id,
        tipo=tipo,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        respaldo_id=respaldo_id,
        es_excepcion=es_excepcion,
        justificacion=justificacion
    )

    # Validar contra reglas de negocio
    resultado = validar_solicitud(db, nueva)
    if not resultado.is_success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=resultado.error
        )

    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva
