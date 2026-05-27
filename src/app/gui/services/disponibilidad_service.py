from typing import Any, cast

import httpx
import streamlit as st

from app.gui.services.auth_service import AuthService
from app.gui.utils.logger import log_gui_action


class DisponibilidadService:
    """Servicio para consultar el calendario de disponibilidad anónimo."""
    
    def __init__(self, base_url: str = "http://api:8000") -> None:
        self.base_url = base_url
        self.auth = AuthService(base_url)

    @log_gui_action("DisponibilidadService")
    def consultar(self, anio: int, mes: int) -> list[dict[str, Any]]:
        """Obtiene los estados de disponibilidad para un mes específico."""
        try:
            # Aunque el endpoint no requiere PII, usamos auth para asegurar que es empleado
            headers = self.auth.get_auth_headers()
            params = {"anio": anio, "mes": mes}
            
            with httpx.Client(base_url=self.base_url) as client:
                response = client.get(
                    "/disponibilidad", 
                    params=params, 
                    headers=headers
                )
                
                if response.status_code == 200:
                    return cast(list[dict[str, Any]], response.json())
                return []
        except Exception as e:
            st.error(f"Error al consultar disponibilidad: {str(e)}")
            return []
