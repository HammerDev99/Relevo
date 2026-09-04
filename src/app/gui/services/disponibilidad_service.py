from typing import Any, cast

from app.gui.services.base_service import BaseAPIService
from app.gui.utils.logger import log_gui_action


class DisponibilidadService(BaseAPIService):
    """Servicio para consultar el calendario de disponibilidad."""

    @log_gui_action("DisponibilidadService")
    def consultar(self, anio: int, mes: int) -> list[dict[str, Any]]:
        """Obtiene los estados de disponibilidad para un mes específico.

        El endpoint no exige sesión, pero se envían las cabeceras: con sesión
        la respuesta incluye nombres y `estado_grupo_propio` (RN5).
        """
        datos = self._get_json(
            "/disponibilidad",
            params={"anio": anio, "mes": mes},
            por_defecto=[],
            mostrar_error=True,
            mensaje_error="Error al consultar disponibilidad",
        )
        return cast(list[dict[str, Any]], datos)
