import streamlit as st

from app.gui import session_keys


def require_auth() -> None:
    """Detiene la ejecución de la página si el usuario no está autenticado."""
    if not st.session_state.get(session_keys.IS_AUTHENTICATED, False):
        st.warning("⚠️ Debes iniciar sesión para acceder a esta sección.")
        st.stop()
