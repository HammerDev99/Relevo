from typing import Any, cast

import streamlit as st

from app.gui.services.base_service import BaseAPIService
from app.gui.utils.logger import log_gui_action


class CoordinacionService(BaseAPIService):
    """Servicio para acciones administrativas (Panel de Coordinación)."""

    # --- Gestión de Solicitudes ---

    @log_gui_action("CoordinacionService")
    def listar_todas(self) -> list[dict[str, Any]]:
        """Obtiene todas las solicitudes del sistema (Audit Log)."""
        datos = self._get_json(
            "/coordinacion/solicitudes", por_defecto=[], mostrar_error=True,
            mensaje_error="Error al listar solicitudes",
        )
        return cast(list[dict[str, Any]], datos)

    @log_gui_action("CoordinacionService")
    def listar_pendientes(self) -> list[dict[str, Any]]:
        """Filtra las solicitudes pendientes de procesar."""
        todas = self.listar_todas()
        return [s for s in todas if s["estado"] == "pendiente"]

    @log_gui_action("CoordinacionService")
    def procesar(self, solicitud_id: int, estado: str) -> bool:
        """Aprueba, rechaza o anula una solicitud."""
        respuesta = self._request(
            "POST", f"/coordinacion/solicitudes/{solicitud_id}/procesar",
            data={"nuevo_estado": estado},
        )
        if respuesta is None:
            return False

        if respuesta.status_code == 200:
            st.success(f"Solicitud marcada como {estado}.")
            return True

        st.error(f"Error: {self._detalle_error(respuesta, 'Error al procesar')}")
        return False

    # --- Gestión de Usuarios ---

    @log_gui_action("CoordinacionService")
    def listar_usuarios(self) -> list[dict[str, Any]]:
        """Lista el personal para administración."""
        datos = self._get_json(
            "/coordinacion/usuarios", por_defecto=[], mostrar_error=True,
            mensaje_error="Error al listar usuarios",
        )
        return cast(list[dict[str, Any]], datos)

    @log_gui_action("CoordinacionService")
    def crear_usuario(self, data: dict[str, Any]) -> bool:
        """Registra un nuevo empleado (SPEC-S18-B3)."""
        respuesta = self._request("POST", "/coordinacion/usuarios", json=data)
        if respuesta is None:
            return False

        if respuesta.status_code == 200:
            return True

        if respuesta.status_code == 422:
            st.error(
                "Datos inválidos. Verifica el correo "
                "y que la contraseña tenga al menos 8 caracteres."
            )
        else:
            st.error(f"Error: {self._detalle_error(respuesta, 'Error al crear el usuario')}")
        return False

    @log_gui_action("CoordinacionService")
    def actualizar_usuario(self, usuario_id: int, data: dict[str, Any]) -> bool:
        """Actualiza rol, estado o grupos de un usuario."""
        respuesta = self._request(
            "PATCH", f"/coordinacion/usuarios/{usuario_id}", json=data, mostrar_error=False
        )
        return respuesta is not None and respuesta.status_code == 200

    @log_gui_action("CoordinacionService")
    def eliminar_usuario(self, usuario_id: int) -> bool:
        """Elimina un usuario y sus registros asociados en cascada."""
        respuesta = self._request("DELETE", f"/coordinacion/usuarios/{usuario_id}")
        if respuesta is None:
            return False

        if respuesta.status_code == 200:
            st.success("Usuario y sus registros asociados eliminados en cascada.")
            return True

        st.error(f"Error: {self._detalle_error(respuesta, 'Error al eliminar')}")
        return False

    # --- Gestión de Grupos ---

    @log_gui_action("CoordinacionService")
    def listar_grupos(self) -> list[dict[str, Any]]:
        """Lista los grupos de trabajo."""
        datos = self._get_json("/coordinacion/grupos", por_defecto=[])
        return cast(list[dict[str, Any]], datos)

    @log_gui_action("CoordinacionService")
    def crear_grupo(self, nombre: str, min_presentes: int) -> bool:
        """Crea un grupo de trabajo."""
        respuesta = self._request(
            "POST", "/coordinacion/grupos",
            json={"nombre": nombre, "min_presentes": min_presentes},
            mostrar_error=False,
        )
        return respuesta is not None and respuesta.status_code == 200

    @log_gui_action("CoordinacionService")
    def actualizar_grupo(self, grupo_id: int, data: dict[str, Any]) -> bool:
        """Actualiza los parámetros de un grupo (min_presentes, nombre)."""
        respuesta = self._request(
            "PATCH", f"/coordinacion/grupos/{grupo_id}", json=data, mostrar_error=False
        )
        return respuesta is not None and respuesta.status_code == 200

    # --- Configuración Global ---

    @log_gui_action("CoordinacionService")
    def obtener_configuracion(self) -> dict[str, Any]:
        """Lee la configuración global de la aplicación."""
        datos = self._get_json("/configuracion", por_defecto={}, autenticado=False)
        return cast(dict[str, Any], datos)

    @log_gui_action("CoordinacionService")
    def actualizar_configuracion(self, data: dict[str, Any]) -> bool:
        """Actualiza la configuración global."""
        respuesta = self._request(
            "PATCH", "/configuracion", json=data, mostrar_error=False
        )
        return respuesta is not None and respuesta.status_code == 200
