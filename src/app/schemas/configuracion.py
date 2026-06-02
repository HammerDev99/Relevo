from pydantic import BaseModel, ConfigDict


class ConfiguracionRead(BaseModel):
    mostrar_grupos_tooltip: bool

    model_config = ConfigDict(frozen=True, from_attributes=True)


class ConfiguracionUpdate(BaseModel):
    mostrar_grupos_tooltip: bool
