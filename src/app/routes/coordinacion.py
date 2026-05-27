from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Form, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import get_coordinador
from app.database import get_db
from app.models import Empleado, Grupo, Solicitud
from app.schemas.grupos import GrupoCreate, GrupoRead, GrupoUpdate
from app.schemas.solicitudes import SolicitudRead
from app.schemas.usuarios import UsuarioRead, UsuarioUpdate

router = APIRouter(prefix="/coordinacion", tags=["coordinacion"])

# --- Gestión de Solicitudes (Audit Log) ---

@router.get("/solicitudes", response_model=list[SolicitudRead])
def listar_todas(
    db: Session = Depends(get_db),
    admin: Empleado = Depends(get_coordinador)
) -> list[SolicitudRead]:
    """Lista todas las solicitudes del sistema (Audit Log)."""
    query = select(Solicitud).order_by(Solicitud.creada_en.desc())
    solicitudes = db.scalars(query).all()
    
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
    """Anula o cambia el estado de una solicitud (Audit/Admin)."""
    solicitud = db.get(Solicitud, solicitud_id)
    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    
    if nuevo_estado not in ["aprobada", "rechazada", "anulada"]:
        raise HTTPException(status_code=400, detail="Estado inválido")
        
    solicitud.estado = nuevo_estado
    solicitud.procesada_en = datetime.now(UTC)
    solicitud.procesada_por_id = admin.id
    
    db.commit()
    return {"message": f"Solicitud {nuevo_estado} exitosamente"}

# --- Gestión de Usuarios ---

@router.get("/usuarios", response_model=list[UsuarioRead])
def admin_listar_usuarios(
    db: Session = Depends(get_db),
    admin: Empleado = Depends(get_coordinador)
) -> list[Empleado]:
    """Lista todos los usuarios para administración."""
    return list(db.scalars(select(Empleado)).all())

@router.patch("/usuarios/{usuario_id}", response_model=UsuarioRead)
def actualizar_usuario(
    usuario_id: int,
    data: UsuarioUpdate,
    db: Session = Depends(get_db),
    admin: Empleado = Depends(get_coordinador)
) -> Empleado:
    """Actualiza rol, estado o grupos de un usuario."""
    user = db.get(Empleado, usuario_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if data.rol is not None:
        user.rol = data.rol
    if data.activo is not None:
        user.activo = data.activo
    
    if data.grupo_ids is not None:
        # Actualizar relaciones M:N
        nuevos_grupos = db.scalars(select(Grupo).where(Grupo.id.in_(data.grupo_ids))).all()
        user.grupos = list(nuevos_grupos)
        
    db.commit()
    db.refresh(user)
    return user

# --- Gestión de Grupos ---

@router.get("/grupos", response_model=list[GrupoRead])
def listar_grupos(
    db: Session = Depends(get_db),
    admin: Empleado = Depends(get_coordinador)
) -> list[Grupo]:
    return list(db.scalars(select(Grupo)).all())

@router.post("/grupos", response_model=GrupoRead)
def crear_grupo(
    data: GrupoCreate,
    db: Session = Depends(get_db),
    admin: Empleado = Depends(get_coordinador)
) -> Grupo:
    nuevo = Grupo(**data.model_dump())
    db.add(nuevo)
    try:
        db.commit()
        db.refresh(nuevo)
        return nuevo
    except Exception as err:
        db.rollback()
        raise HTTPException(status_code=400, detail="Error al crear el grupo") from err

@router.patch("/grupos/{grupo_id}", response_model=GrupoRead)
def actualizar_grupo(
    grupo_id: int,
    data: GrupoUpdate,
    db: Session = Depends(get_db),
    admin: Empleado = Depends(get_coordinador)
) -> Grupo:
    grupo = db.get(Grupo, grupo_id)
    if not grupo:
        raise HTTPException(status_code=404, detail="Grupo no encontrado")
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(grupo, key, value)
        
    db.commit()
    db.refresh(grupo)
    return grupo
