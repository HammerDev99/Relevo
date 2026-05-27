import streamlit as st
from services.auth_service import AuthService
from gui import session_keys

# Configuración de página (Professional Style)
st.set_page_config(
    page_title="Relevo — Gestión de Ausencias",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados (Replicando estética limpia)
st.markdown("""
    <style>
    .main {
        background-color: #f5f7f9;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #004b87;
        color: white;
    }
    .stTextInput>div>div>input {
        border-radius: 5px;
    }
    </style>
    """, unsafe_allow_stdio=True)

def main():
    auth = AuthService()

    # --- Lógica de Autenticación ---
    if not auth.is_authenticated:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image("https://www.ramajudicial.gov.co/image/layout_set_logo?img_id=11303&t=1716744000000", width=200)
            st.title("Sistema Relevo")
            st.subheader("Control de Vacaciones y Permisos")
            
            with st.form("login_form"):
                email = st.text_input("Correo Institucional")
                password = st.text_input("Contraseña", type="password")
                submit = st.form_submit_button("Iniciar Sesión")
                
                if submit:
                    if auth.login(email, password):
                        st.success("Acceso concedido")
                        st.rerun()
    else:
        # --- App Autenticada ---
        with st.sidebar:
            st.title("📅 Relevo")
            st.write(f"Usuario: **{st.session_state.get(session_keys.USER_EMAIL)}**")
            st.write(f"Rol: `{auth.user_role.upper()}`")
            st.divider()
            
            # Navegación manual (Streamlit Multi-page apps automáticas se pueden ocultar)
            if st.button("Cerrar Sesión"):
                auth.logout()

        st.title("Bienvenido al Sistema Relevo")
        st.info("Estamos configurando las páginas del portal. Por ahora, el login es funcional.")
        
        # Dashboard Inicial
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Saldo Vacaciones", "22 días", "Disponibles")
        with col2:
            st.metric("Saldo Permisos", "3 días", "Este mes")

if __name__ == "__main__":
    # Necesitamos añadir el path actual para que los imports funcionen si se corre desde app.py
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    main()
