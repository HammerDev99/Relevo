from typing import Any, cast

import httpx
import streamlit as st

from app.gui.services.auth_service import AuthService
from app.gui.utils.logger import log_gui_action


class CoordinacionService:
    """Servicio para acciones administrativas (Panel de Coordinación)."""

    def __init__(self, base_url: str = "http://api:8000") -> None:
        self.base_url = base_url
        self.auth = AuthService(base_url)

    @log_gui_action("CoordinacionService")
    def listar_pendientes(self) -> list[dict[str, Any]]:
        """Obtiene todas las solicitudes pendientes."""
        try:
            headers = self.auth.get_auth_headers()
            with httpx.Client(base_url=self.base_url) as client:
                response = client.get("/coordinacion/solicitudes/pendientes", headers=headers)
                if response.status_code == 200:
                    return cast(list[dict[str, Any]], response.json())
                elif response.status_code == 403:
                    st.error("No tienes permisos de coordinación.")
                return []
        except Exception as e:
            st.error(f"Error al listar pendientes: {str(e)}")
            return []

    @log_gui_action("CoordinacionService")
    def procesar(self, solicitud_id: int, estado: str) -> bool:
        """Aprueba o rechaza una solicitud."""
        try:
            headers = self.auth.get_auth_headers()
            with httpx.Client(base_url=self.base_url) as client:
                response = client.post(
                    f"/coordinacion/solicitudes/{solicitud_id}/procesar",
                    data={"nuevo_estado": estado},
                    headers=headers
                )
                if response.status_code == 200:
                    st.success(f"Solicitud {estado} correctamente.")
                    return True
                else:
                    err = response.json().get("detail", "Error al procesar")
                    st.error(f"Error: {err}")
                    return False
        except Exception as e:
            st.error(f"Error de conexión: {str(e)}")
            return False
