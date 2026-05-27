import httpx
import streamlit as st
from typing import Optional, Dict, Any
from ..gui import session_keys

class AuthService:
    """Servicio para gestionar la autenticación con el backend FastAPI."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url

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
                    data = response.json()
                    # En este MVP, la cookie la maneja el navegador/httpx si estuviéramos en JS,
                    # pero en Streamlit (Server-side) necesitamos extraerla o confiar en el token
                    # si el backend devolviera uno explícito. 
                    # Como usamos cookies firmadas, guardaremos el estado de éxito.
                    st.session_state[session_keys.IS_AUTHENTICATED] = True
                    st.session_state[session_keys.USER_EMAIL] = email
                    st.session_state[session_keys.USER_ROLE] = data.get("rol", "empleado")
                    
                    # Guardamos las cookies de la respuesta para futuras peticiones
                    st.session_state[session_keys.AUTH_TOKEN] = response.cookies.get("session")
                    return True
                else:
                    st.error(f"Error de login: {response.json().get('detail', 'Credenciales inválidas')}")
                    return False
        except Exception as e:
            st.error(f"Error de conexión con el servidor: {str(e)}")
            return False

    def logout(self):
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
        return st.session_state.get(session_keys.IS_AUTHENTICATED, False)

    @property
    def user_role(self) -> str:
        return st.session_state.get(session_keys.USER_ROLE, "empleado")

    def get_auth_headers(self) -> Dict[str, str]:
        """Retorna los headers/cookies necesarios para peticiones autenticadas."""
        token = st.session_state.get(session_keys.AUTH_TOKEN)
        if token:
            return {"Cookie": f"session={token}"}
        return {}
