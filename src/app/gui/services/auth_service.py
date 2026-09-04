from typing import Any, cast

import streamlit as st

from app.gui import session_keys
from app.gui.services.base_service import BaseAPIService
from app.gui.utils.logger import log_gui_action
from app.roles import ROL_EMPLEADO


class AuthService(BaseAPIService):
    """Servicio para gestionar la autenticación con el backend FastAPI."""

    @log_gui_action("AuthService")
    def login(self, email: str, password: str) -> bool:
        """Intenta iniciar sesión y guarda el estado en session_state."""
        respuesta = self._request(
            "POST", "/login",
            data={"correo": email, "password": password},
            autenticado=False,
            follow_redirects=True,
            mostrar_error=False,
        )
        if respuesta is None:
            st.error("Error de conexión con el servidor")
            return False

        if respuesta.status_code != 200:
            st.error(
                f"Error de login: {self._detalle_error(respuesta, 'Credenciales inválidas')}"
            )
            return False

        data = cast(dict[str, Any], respuesta.json())
        st.session_state[session_keys.IS_AUTHENTICATED] = True
        st.session_state[session_keys.USER_EMAIL] = email
        st.session_state[session_keys.USER_ROLE] = data.get("rol", ROL_EMPLEADO)
        st.session_state[session_keys.AUTH_TOKEN] = respuesta.cookies.get("session")
        return True

    @log_gui_action("AuthService")
    def logout(self) -> None:
        """Limpia la sesión local."""
        for key in [
            session_keys.IS_AUTHENTICATED,
            session_keys.USER_EMAIL,
            session_keys.USER_ROLE,
            session_keys.AUTH_TOKEN,
        ]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

    @log_gui_action("AuthService")
    def get_me(self) -> dict[str, Any] | None:
        """Obtiene el perfil del usuario actual.

        No existe un endpoint `/me`: se localiza por correo en `/usuarios`.
        """
        usuarios = self._get_json("/usuarios", por_defecto=None)
        if usuarios is None:
            return None

        email = st.session_state.get(session_keys.USER_EMAIL)
        for u in cast(list[dict[str, Any]], usuarios):
            if u["correo"] == email:
                return u
        return None

    @property
    def is_authenticated(self) -> bool:
        return cast(bool, st.session_state.get(session_keys.IS_AUTHENTICATED, False))

    @property
    def user_role(self) -> str:
        return cast(str, st.session_state.get(session_keys.USER_ROLE, ROL_EMPLEADO))

    @log_gui_action("AuthService")
    def change_password(self, current_password: str, new_password: str) -> bool:
        """SPEC-S14-C4: Cambia la contraseña del usuario actual."""
        respuesta = self._request(
            "PATCH", "/usuarios/me/password",
            json={"current_password": current_password, "new_password": new_password},
            mensaje_error="Error al cambiar contraseña",
        )
        return respuesta is not None and respuesta.status_code == 200
