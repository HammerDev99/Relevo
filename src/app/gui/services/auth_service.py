from typing import Any, cast

import httpx
import streamlit as st

from app.gui import session_keys
from app.gui.utils.logger import log_gui_action


class AuthService:
    """Servicio para gestionar la autenticación con el backend FastAPI."""
    
    def __init__(self, base_url: str = "http://api:8000"):
        # En Docker, el servicio api es accesible por su nombre
        self.base_url = base_url

    @log_gui_action("AuthService")
    def login(self, email: str, password: str) -> bool:
        """Intenta iniciar sesión y guarda el estado en session_state."""
        try:
            with httpx.Client(base_url=self.base_url) as client:
                response = client.post(
                    "/login", 
                    data={"correo": email, "password": password},
                    follow_redirects=True
                )
                
                if response.status_code == 200:
                    data = cast(dict[str, Any], response.json())
                    st.session_state[session_keys.IS_AUTHENTICATED] = True
                    st.session_state[session_keys.USER_EMAIL] = email
                    st.session_state[session_keys.USER_ROLE] = data.get("rol", "empleado")
                    st.session_state[session_keys.AUTH_TOKEN] = response.cookies.get("session")
                    return True
                else:
                    err = response.json().get("detail", "Credenciales inválidas")
                    st.error(f"Error de login: {err}")
                    return False
        except Exception as e:
            st.error(f"Error de conexión con el servidor: {str(e)}")
            return False

    @log_gui_action("AuthService")
    def logout(self) -> None:
        """Limpia la sesión local."""
        for key in [
            session_keys.IS_AUTHENTICATED, 
            session_keys.USER_EMAIL, 
            session_keys.USER_ROLE, 
            session_keys.AUTH_TOKEN
        ]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

    @property
    def is_authenticated(self) -> bool:
        return cast(bool, st.session_state.get(session_keys.IS_AUTHENTICATED, False))

    @property
    def user_role(self) -> str:
        return cast(str, st.session_state.get(session_keys.USER_ROLE, "empleado"))

    def get_auth_headers(self) -> dict[str, str]:
        """Retorna los headers/cookies necesarios para peticiones autenticadas."""
        token = st.session_state.get(session_keys.AUTH_TOKEN)
        if token:
            return {"Cookie": f"session={token}"}
        return {}
