import streamlit as st

from app.gui.services.auth_service import AuthService


def show() -> None:
    """SPEC-S14-C4: Página de perfil de usuario con cambio de contraseña."""
    st.title("👤 Mi Perfil")

    # CSS para diseño responsivo
    st.markdown("""
        <style>
        @media (max-width: 640px) {
            [data-testid="stHorizontalBlock"] {
                flex-direction: column !important;
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
                        # Limpiar campos
                        st.session_state.current_password = ""
                        st.session_state.new_password = ""
                        st.session_state.confirm_password = ""
                        st.rerun()
                    else:
                        st.error(
                            "❌ Error al actualizar la contraseña. "
                            "Verifique que la contraseña actual sea correcta."
                        )

        with col_btn2:
            if st.button("Cancelar"):
                st.session_state.current_password = ""
                st.session_state.new_password = ""
                st.session_state.confirm_password = ""
                st.rerun()

    st.info("💡 Recuerde usar una contraseña segura con al menos 6 caracteres.")
