from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.roles import ROL_EMPLEADO, RolUsuario

# Longitud mínima de la contraseña inicial asignada por Coordinación (SPEC-S18-B1)
LONGITUD_MINIMA_PASSWORD = 8


class UsuarioBase(BaseModel):
    nombre: str
    correo: EmailStr
    rol: str
    activo: bool = True

    model_config = ConfigDict(frozen=True, from_attributes=True)


class UsuarioRead(UsuarioBase):
    id: int
    creado_en: datetime
    grupo_ids: list[int] = []


class UsuarioCreate(BaseModel):
    """Alta de empleado desde el panel de Coordinación (SPEC-S18-B1)."""

    nombre: str = Field(min_length=1, max_length=100)
    correo: EmailStr
    password: str = Field(min_length=LONGITUD_MINIMA_PASSWORD, max_length=128)
    rol: RolUsuario = ROL_EMPLEADO
    grupo_ids: list[int] = []

    model_config = ConfigDict(frozen=True)


class UsuarioLogin(BaseModel):
    correo: EmailStr
    password: str

    model_config = ConfigDict(frozen=True)


class UsuarioUpdate(BaseModel):
    # SPEC-S19-A1: misma whitelist que UsuarioCreate — antes era `str` y
    # aceptaba roles arbitrarios que rompian get_coordinador.
    rol: RolUsuario | None = None
    activo: bool | None = None
    grupo_ids: list[int] | None = None

    model_config = ConfigDict(frozen=True)


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str

    model_config = ConfigDict(frozen=True)
