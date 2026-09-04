from typing import Any, cast

import httpx
import streamlit as st

from app.gui.services.auth_service import AuthService
from app.gui.utils.logger import log_gui_action


class CoordinacionService:
    """Servicio para acciones administrativas (Panel de Coordinación)."""

    def __init__(self, base_url: str = "http://relevo-api:8000") -> None:
        self.base_url = base_url
        self.auth = AuthService(base_url)

    @log_gui_action("CoordinacionService")
    def listar_todas(self) -> list[dict[str, Any]]:
        """Obtiene todas las solicitudes del sistema (Audit Log)."""
        try:
            headers = self.auth.get_auth_headers()
            with httpx.Client(base_url=self.base_url) as client:
                response = client.get("/coordinacion/solicitudes", headers=headers)
                if response.status_code == 200:
                    return cast(list[dict[str, Any]], response.json())
                return []
        except Exception as e:
            st.error(f"Error al listar solicitudes: {str(e)}")
            return []

    @log_gui_action("CoordinacionService")
    def listar_pendientes(self) -> list[dict[str, Any]]:
        """DEPRECATED: Ahora se usa autogestión, pero mantenemos por compatibilidad."""
        todas = self.listar_todas()
        return [s for s in todas if s["estado"] == "pendiente"]

    @log_gui_action("CoordinacionService")
    def procesar(self, solicitud_id: int, estado: str) -> bool:
        """Anula o cambia el estado de una solicitud."""
        try:
            headers = self.auth.get_auth_headers()
            with httpx.Client(base_url=self.base_url) as client:
                response = client.post(
                    f"/coordinacion/solicitudes/{solicitud_id}/procesar",
                    data={"nuevo_estado": estado},
                    headers=headers
                )
                if response.status_code == 200:
                    st.success(f"Solicitud marcada como {estado}.")
                    return True
                else:
                    err = response.json().get("detail", "Error al procesar")
                    st.error(f"Error: {err}")
                    return False
        except Exception as e:
            st.error(f"Error de conexión: {str(e)}")
            return False

    # --- Gestión de Usuarios ---

    @log_gui_action("CoordinacionService")
    def listar_usuarios(self) -> list[dict[str, Any]]:
        try:
            headers = self.auth.get_auth_headers()
            with httpx.Client(base_url=self.base_url) as client:
                response = client.get("/coordinacion/usuarios", headers=headers)
                if response.status_code == 200:
                    return cast(list[dict[str, Any]], response.json())
                return []
        except Exception as e:
            st.error(f"Error al listar usuarios: {str(e)}")
            return []

    @log_gui_action("CoordinacionService")
    def crear_usuario(self, data: dict[str, Any]) -> bool:
        """Registra un nuevo empleado (SPEC-S18-B3)."""
        try:
            headers = self.auth.get_auth_headers()
            with httpx.Client(base_url=self.base_url) as client:
                response = client.post(
                    "/coordinacion/usuarios",
                    json=data,
                    headers=headers
                )
                if response.status_code == 200:
                    return True

                if response.status_code == 422:
                    st.error(
                        "Datos inválidos. Verifica el correo "
                        "y que la contraseña tenga al menos 8 caracteres."
                    )
                else:
                    detalle = response.json().get("detail", "Error al crear el usuario")
                    st.error(f"Error: {detalle}")
                return False
        except Exception as e:
            st.error(f"Error de conexión: {str(e)}")
            return False

    @log_gui_action("CoordinacionService")
    def actualizar_usuario(self, usuario_id: int, data: dict[str, Any]) -> bool:
        try:
            headers = self.auth.get_auth_headers()
            with httpx.Client(base_url=self.base_url) as client:
                response = client.patch(
                    f"/coordinacion/usuarios/{usuario_id}",
                    json=data,
                    headers=headers
                )
                return response.status_code == 200
        except Exception:
            return False

    @log_gui_action("CoordinacionService")
    def eliminar_usuario(self, usuario_id: int) -> bool:
        try:
            headers = self.auth.get_auth_headers()
            with httpx.Client(base_url=self.base_url) as client:
                response = client.delete(
                    f"/coordinacion/usuarios/{usuario_id}",
                    headers=headers
                )
                if response.status_code == 200:
                    st.success("Usuario y sus registros asociados eliminados en cascada.")
                    return True
                else:
                    err = response.json().get("detail", "Error al eliminar")
                    st.error(f"Error: {err}")
                    return False
        except Exception as e:
            st.error(f"Error de conexión: {str(e)}")
            return False

    # --- Gestión de Grupos ---

    @log_gui_action("CoordinacionService")
    def listar_grupos(self) -> list[dict[str, Any]]:
        try:
            headers = self.auth.get_auth_headers()
            with httpx.Client(base_url=self.base_url) as client:
                response = client.get("/coordinacion/grupos", headers=headers)
                if response.status_code == 200:
                    return cast(list[dict[str, Any]], response.json())
                return []
        except Exception:
            return []

    @log_gui_action("CoordinacionService")
    def crear_grupo(self, nombre: str, min_presentes: int) -> bool:
        try:
            headers = self.auth.get_auth_headers()
            with httpx.Client(base_url=self.base_url) as client:
                response = client.post(
                    "/coordinacion/grupos",
                    json={"nombre": nombre, "min_presentes": min_presentes},
                    headers=headers
                )
                return response.status_code == 200
        except Exception:
            return False

    # --- Configuración Global ---

    @log_gui_action("CoordinacionService")
    def obtener_configuracion(self) -> dict[str, Any]:
        try:
            with httpx.Client(base_url=self.base_url) as client:
                response = client.get("/configuracion")
                if response.status_code == 200:
                    return cast(dict[str, Any], response.json())
                return {}
        except Exception:
            return {}

    @log_gui_action("CoordinacionService")
    def actualizar_configuracion(self, data: dict[str, Any]) -> bool:
        try:
            headers = self.auth.get_auth_headers()
            with httpx.Client(base_url=self.base_url) as client:
                response = client.patch("/configuracion", json=data, headers=headers)
                return response.status_code == 200
        except Exception:
            return False

    @log_gui_action("CoordinacionService")
    def actualizar_grupo(self, grupo_id: int, data: dict[str, Any]) -> bool:
        try:
            headers = self.auth.get_auth_headers()
            with httpx.Client(base_url=self.base_url) as client:
                response = client.patch(
                    f"/coordinacion/grupos/{grupo_id}",
                    json=data,
                    headers=headers
                )
                return response.status_code == 200
        except Exception:
            return False
