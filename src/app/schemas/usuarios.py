from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


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


class UsuarioLogin(BaseModel):
    correo: EmailStr
    password: str

    model_config = ConfigDict(frozen=True)


class UsuarioUpdate(BaseModel):
    rol: str | None = None
    activo: bool | None = None
    grupo_ids: list[int] | None = None

    model_config = ConfigDict(frozen=True)


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str

    model_config = ConfigDict(frozen=True)
