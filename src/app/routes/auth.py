from fastapi import APIRouter, Depends, Form, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import create_session_token, get_empleado_actual, verify_password
from app.database import get_db
from app.models import Empleado
from app.schemas.usuarios import UsuarioRead

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
