from pydantic import BaseModel, ConfigDict


class GrupoBase(BaseModel):
    nombre: str
    min_presentes: int = 1

    model_config = ConfigDict(frozen=True, from_attributes=True)

class GrupoRead(GrupoBase):
    id: int

class GrupoCreate(GrupoBase):
    pass

class GrupoUpdate(BaseModel):
    nombre: str | None = None
    min_presentes: int | None = None

    model_config = ConfigDict(frozen=True)
