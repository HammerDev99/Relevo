import streamlit as st

from app.gui.services.auth_service import AuthService
from app.gui.utils.auth_guard import require_auth


def show() -> None:
    require_auth()
    st.title("👤 Mi Perfil")

    # SPEC-S15-C7: CSS mejorado para diseño móvil responsivo
    st.markdown("""
        <style>
        /* Mobile optimizations */
        @media (max-width: 768px) {
            /* Ajustar columnas para apilarse en móvil */
            [data-testid="stHorizontalBlock"] > div {
                flex-direction: column !important;
                width: 100% !important;
            }
            
            /* Ajustar tamaño de contenedores */
            [data-testid="stContainer"] {
                padding: 0.5rem !important;
            }
            
            /* Ajustar tamaño de texto en móvil */
            h1 { font-size: 1.5rem !important; }
            h2 { font-size: 1.25rem !important; }
            
            /* Ajustar ancho de elementos en móvil */
            [data-testid="stColumn"] {
                width: 100% !important;
                margin-bottom: 0.5rem !important;
            }
            
            /* Ajustar tamaño de inputs en móvil */
            input, select, textarea {
                font-size: 16px !important;  /* Evitar zoom en iOS */
            }
            
            /* Ajustar espaciado en móvil */
            .css-1d391kg {
                padding: 0.5rem !important;
            }
            
            /* Ajustar tamaño de botones en móvil */
            .stButton > button {
                width: 100% !important;
                padding: 0.75rem !important;
                font-size: 1rem !important;
            }
        }
        
        /* Tablet optimizations */
        @media (min-width: 769px) and (max-width: 1024px) {
            [data-testid="stHorizontalBlock"] > div {
                padding: 0.5rem !important;
            }
        }
        </style>
    """, unsafe_allow_html=True)

    auth = AuthService()
    me = auth.get_me()

    if not me:
        st.error("No se pudo obtener información del usuario")
        return

    # Mostrar información del usuario
    st.subheader("Información Personal")
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("Nombre", value=me.get("nombre", ""), disabled=True)
    with col2:
        st.text_input("Correo", value=me.get("correo", ""), disabled=True)

    st.text_input("Rol", value=me.get("rol", ""), disabled=True)

    st.divider()

    # Sección de cambio de contraseña
    st.subheader("🔐 Cambiar Contraseña")

    with st.expander("Cambiar mi contraseña", expanded=False):
        current_password = st.text_input(
            "Contraseña Actual",
            type="password",
            key="current_password"
        )
        new_password = st.text_input(
            "Nueva Contraseña",
            type="password",
            key="new_password"
        )
        confirm_password = st.text_input(
            "Confirmar Nueva Contraseña",
            type="password",
            key="confirm_password"
        )

        col_btn1, col_btn2, _ = st.columns([1, 1, 2])
        with col_btn1:
            if st.button("Actualizar Contraseña", type="primary"):
                if not current_password or not new_password:
                    st.error("Por favor complete todos los campos")
                elif new_password != confirm_password:
                    st.error("Las contraseñas nuevas no coinciden")
                elif len(new_password) < 6:
                    st.error("La nueva contraseña debe tener al menos 6 caracteres")
                elif current_password == new_password:
                    st.error("La nueva contraseña debe ser diferente a la actual")
                else:
                    # Llamar al endpoint de cambio de contraseña
                    result = auth.change_password(current_password, new_password)
                    if result:
                        st.success("✅ Contraseña actualizada exitosamente")
                        for k in ["current_password", "new_password", "confirm_password"]:
                            st.session_state.pop(k, None)
                        st.rerun()
                    else:
                        st.error(
                            "❌ Error al actualizar la contraseña. "
                            "Verifique que la contraseña actual sea correcta."
                        )

        with col_btn2:
            if st.button("Cancelar"):
                for k in ["current_password", "new_password", "confirm_password"]:
                    st.session_state.pop(k, None)
                st.rerun()

    st.info("💡 Recuerde usar una contraseña segura con al menos 6 caracteres.")

if __name__ == "__main__":
    show()
