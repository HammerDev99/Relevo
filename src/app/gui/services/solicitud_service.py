from typing import Any

import httpx
import streamlit as st

from .auth_service import AuthService


class SolicitudService:
    """Servicio para gestionar las solicitudes de ausencia con el backend."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.auth = AuthService(base_url)

    def listar_propias(self) -> list[dict[str, Any]]:
        """Obtiene las solicitudes del usuario autenticado."""
        try:
            headers = self.auth.get_auth_headers()
            with httpx.Client(base_url=self.base_url) as client:
                response = client.get("/solicitudes", headers=headers)
                if response.status_code == 200:
                    return response.json()
                return []
        except Exception as e:
            st.error(f"Error al listar solicitudes: {str(e)}")
            return []

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
                    return {"success": True, "data": response.json()}
                else:
                    err = response.json().get("detail", "Error desconocido")
                    return {"success": False, "error": err}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def listar_empleados(self) -> list[dict[str, Any]]:
        """Obtiene lista de empleados activos para el selector de respaldo."""
        try:
            headers = self.auth.get_auth_headers()
            with httpx.Client(base_url=self.base_url) as client:
                response = client.get("/usuarios", headers=headers)
                if response.status_code == 200:
                    return response.json()
                return []
        except Exception as e:
            st.error(f"Error al listar usuarios: {str(e)}")
            return []
