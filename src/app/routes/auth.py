from fastapi import APIRouter, Depends, Form, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import create_session_token, get_empleado_actual, get_password_hash, verify_password
from app.database import get_db
from app.models import Empleado
from app.schemas.usuarios import (
    LONGITUD_MINIMA_PASSWORD,
    PasswordChangeRequest,
    UsuarioRead,
)
from relevo.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["auth"])

@router.post("/login")
def login(
    response: Response,
    correo: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
) -> dict[str, str]:
    """Autentica un empleado y establece la cookie de sesión."""
    query = select(Empleado).where(Empleado.correo == correo, Empleado.activo)
    empleado = db.scalar(query)

    if not empleado or not verify_password(password, empleado.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos"
        )
    
    token = create_session_token({"user_id": empleado.id, "rol": empleado.rol})
    
    response.set_cookie(
        key="session",
        value=token,
        httponly=True,
        samesite="strict",
        secure=False,
    )
    
    return {"message": "Login exitoso", "rol": empleado.rol}

@router.get("/logout")
def logout(response: Response) -> dict[str, str]:
    """Limpia la cookie de sesión."""
    response.delete_cookie("session")
    return {"message": "Logout exitoso"}

@router.get("/usuarios", response_model=list[UsuarioRead])
def listar_usuarios(
    db: Session = Depends(get_db),
    empleado: Empleado = Depends(get_empleado_actual)
) -> list[Empleado]:
    """Retorna lista de empleados activos (para selector de respaldo)."""
    query = select(Empleado).where(Empleado.activo)
    usuarios = db.scalars(query).all()
    return list(usuarios)


@router.patch("/usuarios/me/password")
def cambiar_password(
    request_data: PasswordChangeRequest,
    db: Session = Depends(get_db),
    empleado: Empleado = Depends(get_empleado_actual)
) -> dict[str, str]:
    """Permite al empleado actual cambiar su contraseña verificando la actual."""
    # Verificar que la contraseña actual es correcta
    if not verify_password(request_data.current_password, empleado.password_hash):
        logger.warning(f"Intento fallido de cambio de contraseña para usuario {empleado.correo}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña actual es incorrecta"
        )
    
    # Validar que la nueva contraseña no sea igual a la actual
    if request_data.current_password == request_data.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La nueva contraseña debe ser diferente a la actual"
        )
    
    # Validar longitud mínima de la nueva contraseña
    if len(request_data.new_password) < LONGITUD_MINIMA_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"La nueva contraseña debe tener al menos "
                f"{LONGITUD_MINIMA_PASSWORD} caracteres"
            )
        )
    
    # Actualizar el hash de la contraseña
    empleado.password_hash = get_password_hash(request_data.new_password)
    db.commit()
    
    logger.info(f"Contraseña cambiada exitosamente para usuario {empleado.correo}")
    return {"message": "Contraseña actualizada exitosamente"}
