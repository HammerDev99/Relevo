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


class UsuarioLogin(BaseModel):
    correo: EmailStr
    password: str

    model_config = ConfigDict(frozen=True)
