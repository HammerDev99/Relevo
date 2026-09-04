
import streamlit as st

from app.gui import session_keys
from app.gui.services.auth_service import AuthService
from app.roles import ROL_COORDINACION, ROL_EMPLEADO

# Configuración de página (Professional Style + Mobile Optimized)
st.set_page_config(
    page_title="Relevo — Gestión de Ausencias",
    page_icon="📅",
    layout="wide",  # SPEC-S15-C7: layout wide para mejor responsividad
    initial_sidebar_state="auto"  # SPEC-S15-C7: auto para mejor experiencia móvil
)

# Estilos CSS personalizados (Replicando estética limpia de la Rama Judicial + Mobile)
st.markdown("""
    <style>
    /* General styles */
    .main { background-color: #f5f7f9; }
    .stButton>button {
        border-radius: 5px;
        background-color: #004b87;
        color: white;
        width: 100%;  /* SPEC-S15-C7: Botones full-width en móvil */
    }
    [data-testid="stMetricValue"] { font-size: 24px; }
    
    /* SPEC-S15-C7: Mobile optimizations */
    @media (max-width: 768px) {
        /* Ajustar sidebar para móvil */
        .css-1d391kg {
            width: 100% !important;
        }
        
        /* Ajustar espaciado en móvil */
        .css-1v0mbdj {
            padding: 1rem 0.5rem !important;
        }
        
        /* Ajustar tamaño de fuentes en móvil */
        h1 { font-size: 1.5rem !important; }
        h2 { font-size: 1.25rem !important; }
        h3 { font-size: 1.1rem !important; }
        
        /* Ajustar columnas para apilarse en móvil */
        [data-testid="stHorizontalBlock"] > div {
            flex-direction: column !important;
        }
        
        /* Ajustar ancho de contenedores */
        .css-1lcbmhc {
            max-width: 100% !important;
            padding: 1rem !important;
        }
        
        /* Ajustar tamaño de inputs en móvil */
        input, select, textarea {
            font-size: 16px !important;  /* Evitar zoom en iOS */
        }
    }
    
    /* SPEC-S15-C7: Tablet optimizations */
    @media (min-width: 769px) and (max-width: 1024px) {
        .stButton>button {
            width: auto;  /* Botones normales en tablet */
        }
    }
    </style>
    """, unsafe_allow_html=True)

def main() -> None:
    auth = AuthService()

    # --- Estado Inicial ---
    if session_keys.IS_AUTHENTICATED not in st.session_state:
        st.session_state[session_keys.IS_AUTHENTICATED] = False

    # Páginas siempre definidas
    pg_disponibilidad = st.Page("pages/02_disponibilidad.py", title="Disponibilidad", icon="📅")

    # --- Flujo según autenticación ---
    if not st.session_state[session_keys.IS_AUTHENTICATED]:
        # Sin sesión: solo disponibilidad + formulario de login en sidebar
        pg = st.navigation([pg_disponibilidad])

        with st.sidebar:
            st.image(
                "https://www.ramajudicial.gov.co/image/layout_set_logo?img_id=11303&t=1716744000000",
                width=160,
            )
            st.subheader("Iniciar Sesión")
            with st.form("login_form"):
                email = st.text_input("Correo Institucional")
                password = st.text_input("Contraseña", type="password")
                submitted = st.form_submit_button("Entrar", use_container_width=True)
                if submitted and auth.login(email, password):
                    st.rerun()

        pg.run()

    else:
        # Con sesión: navegación completa
        user_role = st.session_state.get(session_keys.USER_ROLE, ROL_EMPLEADO)

        pg_solicitudes = st.Page("pages/01_solicitudes.py", title="Mis Solicitudes", icon="📑")
        pg_perfil = st.Page("pages/04_perfil.py", title="Mi Perfil", icon="👤")
        pg_coordinacion = st.Page("pages/03_coordinacion.py", title="Panel Control", icon="🛡️")

        pages = [pg_disponibilidad, pg_solicitudes, pg_perfil]
        if user_role == ROL_COORDINACION:
            pages.append(pg_coordinacion)

        pg = st.navigation(pages)

        with st.sidebar:
            st.write(f"Usuario: **{st.session_state.get(session_keys.USER_EMAIL)}**")
            st.write(f"Rol: `{user_role.upper()}`")
            if st.button("Cerrar Sesión"):
                auth.logout()

        pg.run()

if __name__ == "__main__":
    main()
