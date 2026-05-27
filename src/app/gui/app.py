import os
import sys

import streamlit as st
from gui import session_keys
from services.auth_service import AuthService

# Añadir el path actual para que los imports funcionen correctamente
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configuración de página (Professional Style)
st.set_page_config(
    page_title="Relevo — Gestión de Ausencias",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados (Replicando estética limpia de la Rama Judicial)
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button {
        border-radius: 5px;
        background-color: #004b87;
        color: white;
    }
    [data-testid="stMetricValue"] { font-size: 24px; }
    </style>
    """, unsafe_allow_html=True)

def main():
    auth = AuthService()

    # --- Estado Inicial ---
    if session_keys.IS_AUTHENTICATED not in st.session_state:
        st.session_state[session_keys.IS_AUTHENTICATED] = False

    # --- Flujo de Autenticación ---
    if not st.session_state[session_keys.IS_AUTHENTICATED]:
        col1, col2, col3 = st.columns([1, 2, 1])
        LOGO_URL = "https://www.ramajudicial.gov.co/image/layout_set_logo?img_id=11303&t=1716744000000"
        with col2:
            st.image(LOGO_URL, width=200)
            st.title("Sistema Relevo")
            st.subheader("Control de Vacaciones y Permisos")
            
            with st.form("login_form"):
                email = st.text_input("Correo Institucional")
                password = st.text_input("Contraseña", type="password")
                submit = st.form_submit_button("Iniciar Sesión")
                
                if submit and auth.login(email, password):
                    st.success("Acceso concedido")
                    st.rerun()
    else:
        # --- App Autenticada (Navegación Dinámica) ---
        user_role = st.session_state.get(session_keys.USER_ROLE, "empleado")
        
        # Definición de páginas
        pg_solicitudes = st.Page(
            "pages/01_solicitudes.py", 
            title="Mis Solicitudes", 
            icon="📑"
        )
        pg_disponibilidad = st.Page(
            "pages/02_disponibilidad.py", 
            title="Disponibilidad", 
            icon="📅"
        )
        pg_coordinacion = st.Page(
            "pages/03_coordinacion.py", 
            title="Panel Control", 
            icon="🛡️"
        )

        # Filtrar por rol
        pages = [pg_solicitudes, pg_disponibilidad]
        if user_role == "coordinacion":
            pages.append(pg_coordinacion)

        # Ejecutar navegación
        pg = st.navigation(pages)
        
        with st.sidebar:
            st.write(f"Usuario: **{st.session_state.get(session_keys.USER_EMAIL)}**")
            st.write(f"Rol: `{user_role.upper()}`")
            if st.button("Cerrar Sesión"):
                auth.logout()

        pg.run()

if __name__ == "__main__":
    main()
