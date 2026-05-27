from typing import Any, cast

import httpx
import streamlit as st

from app.gui.services.auth_service import AuthService
from app.gui.utils.logger import log_gui_action


class SolicitudService:
    """Servicio para gestionar las solicitudes de ausencia con el backend."""
    
    def __init__(self, base_url: str = "http://api:8000") -> None:
        self.base_url = base_url
        self.auth = AuthService(base_url)

    @log_gui_action("SolicitudService")
    def listar_propias(self) -> list[dict[str, Any]]:
        """Obtiene las solicitudes del usuario autenticado."""
        try:
            headers = self.auth.get_auth_headers()
            with httpx.Client(base_url=self.base_url) as client:
                response = client.get("/solicitudes", headers=headers)
                if response.status_code == 200:
                    return cast(list[dict[str, Any]], response.json())
                return []
        except Exception as e:
            st.error(f"Error al listar solicitudes: {str(e)}")
            return []

    @log_gui_action("SolicitudService")
    def crear(self, data: dict[str, Any]) -> dict[str, Any]:
        """Envía una nueva solicitud al backend."""
        try:
            headers = self.auth.get_auth_headers()
            # FastAPI espera Form data en /solicitudes/nueva
            with httpx.Client(base_url=self.base_url) as client:
                response = client.post(
                    "/solicitudes/nueva", 
                    data=data, 
                    headers=headers
                )
                
                if response.status_code == 200:
                    st.success("Solicitud creada exitosamente")
                    return {"success": True, "data": cast(dict[str, Any], response.json())}
                else:
                    err = cast(dict[str, Any], response.json()).get("detail", "Error desconocido")
                    return {"success": False, "error": err}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @log_gui_action("SolicitudService")
    def listar_empleados(self) -> list[dict[str, Any]]:
        """Obtiene lista de empleados activos para el selector de respaldo."""
        try:
            headers = self.auth.get_auth_headers()
            with httpx.Client(base_url=self.base_url) as client:
                response = client.get("/usuarios", headers=headers)
                if response.status_code == 200:
                    return cast(list[dict[str, Any]], response.json())
                return []
        except Exception as e:
            st.error(f"Error al listar usuarios: {str(e)}")
            return []
