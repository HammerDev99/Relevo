from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import get_coordinador
from app.database import get_db
from app.models import ConfiguracionApp, Empleado
from app.schemas.configuracion import ConfiguracionRead, ConfiguracionUpdate
from relevo.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/configuracion", tags=["configuracion"])


def _get_or_create(db: Session) -> ConfiguracionApp:
    config = db.get(ConfiguracionApp, 1)
    if not config:
        config = ConfiguracionApp(id=1, mostrar_grupos_tooltip=True)
        db.add(config)
        db.commit()
        db.refresh(config)
    return config


@router.get("", response_model=ConfiguracionRead)
def obtener_configuracion(db: Session = Depends(get_db)) -> ConfiguracionApp:
    """Retorna la configuración global de la app (sin autenticación)."""
    return _get_or_create(db)


@router.patch("", response_model=ConfiguracionRead)
def actualizar_configuracion(
    data: ConfiguracionUpdate,
    db: Session = Depends(get_db),
    _: Empleado = Depends(get_coordinador),
) -> ConfiguracionApp:
    """Actualiza la configuración global. Solo coordinadores."""
    config = _get_or_create(db)
    config.mostrar_grupos_tooltip = data.mostrar_grupos_tooltip
    db.commit()
    db.refresh(config)
    logger.info(f"Configuración actualizada: mostrar_grupos_tooltip={data.mostrar_grupos_tooltip}")
    return config
