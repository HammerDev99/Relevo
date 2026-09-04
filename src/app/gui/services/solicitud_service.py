from typing import Any, cast

import streamlit as st

from app.gui.services.base_service import BaseAPIService
from app.gui.utils.logger import log_gui_action


class SolicitudService(BaseAPIService):
    """Servicio para gestionar las solicitudes de ausencia con el backend."""

    @log_gui_action("SolicitudService")
    def listar_propias(self) -> list[dict[str, Any]]:
        """Obtiene las solicitudes del usuario autenticado."""
        datos = self._get_json(
            "/solicitudes", por_defecto=[], mostrar_error=True,
            mensaje_error="Error al listar solicitudes",
        )
        return cast(list[dict[str, Any]], datos)

    @log_gui_action("SolicitudService")
    def crear(self, data: dict[str, Any]) -> dict[str, Any]:
        """Envía una nueva solicitud al backend (el endpoint espera Form data)."""
        respuesta = self._request(
            "POST", "/solicitudes/nueva", data=data, mostrar_error=False
        )
        if respuesta is None:
            return {"success": False, "error": "Error de conexión con el servidor"}

        if respuesta.status_code == 200:
            st.success("Solicitud creada exitosamente")
            return {"success": True, "data": cast(dict[str, Any], respuesta.json())}

        return {
            "success": False,
            "error": self._detalle_error(respuesta, "Error desconocido"),
        }

    @log_gui_action("SolicitudService")
    def listar_empleados(self) -> list[dict[str, Any]]:
        """Obtiene lista de empleados activos para el selector de respaldo."""
        datos = self._get_json(
            "/usuarios", por_defecto=[], mostrar_error=True,
            mensaje_error="Error al listar usuarios",
        )
        return cast(list[dict[str, Any]], datos)

    @log_gui_action("SolicitudService")
    def eliminar_propia(self, solicitud_id: int) -> bool:
        """Elimina una solicitud propia."""
        respuesta = self._request("DELETE", f"/solicitudes/{solicitud_id}")
        if respuesta is None:
            return False

        if respuesta.status_code == 200:
            st.success("Solicitud eliminada.")
            return True

        st.error(f"Error: {self._detalle_error(respuesta, 'Error al eliminar')}")
        return False
