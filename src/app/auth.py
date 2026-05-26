from typing import Any

import bcrypt
from fastapi import Depends, HTTPException, Request, status
from itsdangerous import URLSafeTimedSerializer
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from .models import Empleado

serializer = URLSafeTimedSerializer(settings.SECRET_KEY)

def get_password_hash(password: str) -> str:
    """Retorna el hash bcrypt del password."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si el password coincide con el hash."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

def create_session_token(data: dict[str, Any]) -> str:
    """Crea un token firmado para la sesión."""
    return str(serializer.dumps(data))

def get_session_data(token: str) -> dict[str, Any] | None:
    """Decodifica y valida un token de sesión."""
    try:
        # Expiración configurada en segundos
        return serializer.loads(
            token, 
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    except Exception:
        return None

def get_empleado_actual(request: Request, db: Session = Depends(get_db)) -> Empleado:
    """Dependencia para obtener el empleado autenticado desde la cookie."""
    token = request.cookies.get("session")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado",
            headers={"WWW-Authenticate": "Cookie"},
        )
    
    data = get_session_data(token)
    if not data or "user_id" not in data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesión inválida o expirada",
        )
    
    empleado = db.get(Empleado, data["user_id"])
    if not empleado or not empleado.activo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Empleado no encontrado o inactivo",
        )
    
    return empleado

def get_coordinador(empleado: Empleado = Depends(get_empleado_actual)) -> Empleado:
    """Dependencia para asegurar que el empleado tiene rol de coordinación."""
    if empleado.rol != "coordinacion":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos de coordinación",
        )
    return empleado
