from typing import Any, cast

import bcrypt
from fastapi import Depends, HTTPException, Request, status
from itsdangerous import URLSafeTimedSerializer
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from .models import Empleado
from .roles import ROL_COORDINACION

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
        return cast(dict[str, Any], serializer.loads(
            token, 
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        ))
    except Exception:
        return None

def get_empleado_opcional(request: Request, db: Session = Depends(get_db)) -> Empleado | None:
    """Empleado autenticado desde la cookie, o `None` (SPEC-S19-B3).

    Para endpoints accesibles sin sesión que ajustan su respuesta según haya
    o no usuario, como `/disponibilidad` (RN5).
    """
    token = request.cookies.get("session")
    if not token:
        return None

    data = get_session_data(token)
    if not data or "user_id" not in data:
        return None

    empleado = db.get(Empleado, data["user_id"])
    if not empleado or not empleado.activo:
        return None

    return empleado


def get_empleado_actual(request: Request, db: Session = Depends(get_db)) -> Empleado:
    """Dependencia para obtener el empleado autenticado desde la cookie.

    SPEC-S19-B3: se apoya en `get_empleado_opcional()` y añade el rechazo.
    """
    empleado = get_empleado_opcional(request, db)
    if empleado is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado o sesión inválida",
            headers={"WWW-Authenticate": "Cookie"},
        )
    return empleado

def get_coordinador(empleado: Empleado = Depends(get_empleado_actual)) -> Empleado:
    """Dependencia para asegurar que el empleado tiene rol de coordinación."""
    if empleado.rol != ROL_COORDINACION:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos de coordinación",
        )
    return empleado
