import streamlit as st

from app.gui.services.coordinacion_service import CoordinacionService
from app.gui.utils.auth_guard import require_auth


def show() -> None:
    require_auth()
    st.title("🛡️ Panel de Configuración y Control")
    
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
            h3 { font-size: 1.1rem !important; }
            
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
        }
        
        /* Tablet optimizations */
        @media (min-width: 769px) and (max-width: 1024px) {
            [data-testid="stHorizontalBlock"] > div {
                padding: 0.5rem !important;
            }
        }
        </style>
    """, unsafe_allow_html=True)
    
    service = CoordinacionService()
    
    tab_audit, tab_users, tab_groups, tab_config = st.tabs([
        "📜 Log de Solicitudes",
        "👥 Gestión de Usuarios",
        "🏗️ Configuración de Grupos",
        "⚙️ Configuración",
    ])

    # --- TAB 1: LOG DE SOLICITUDES ---
    with tab_audit:
        st.subheader("Auditoría de Movimientos")
        todas = service.listar_todas()
        if not todas:
            st.info("No hay solicitudes en el sistema.")
        else:
            for s in todas:
                with st.container(border=True):
                    c1, c2, c3 = st.columns([2, 2, 1])
                    with c1:
                        st.write(f"👤 **{s['empleado_nombre']}**")
                        st.caption(f"ID: {s['id']} | {s['tipo'].upper()}")
                    with c2:
                        st.write(f"📅 {s['fecha_inicio']} a {s['fecha_fin']}")
                        if s["es_excepcion"]:
                            st.warning("⚠️ Trámite Excepcional")
                    with c3:
                        st.write(f"Estado: **{s['estado'].upper()}**")
                        if s["estado"] == "aprobada" \
                           and st.button("Anular", key=f"anul_{s['id']}") \
                           and service.procesar(s["id"], "anulada"):
                            st.rerun()

    # --- TAB 2: GESTIÓN DE USUARIOS ---
    with tab_users:
        st.subheader("Personal de la Oficina")
        usuarios = service.listar_usuarios()
        grupos = service.listar_grupos()
        opciones_grupos = {g["nombre"]: g["id"] for g in grupos}
        
        for u in usuarios:
            with st.expander(f"👤 {u['nombre']} ({u['rol']})"), st.form(f"form_user_{u['id']}"):
                new_rol = st.selectbox("Rol", ["empleado", "coordinacion"], 
                                     index=0 if u["rol"]=="empleado" else 1)
                new_activo = st.toggle("Activo", value=u["activo"])
                
                # Selección de grupos (M:N)
                mis_grupos_nombres = [g["nombre"] for g in grupos 
                                      if g["id"] in u.get("grupo_ids", [])]
                selected_grupos = st.multiselect("Grupos de Trabajo", 
                                               options=list(opciones_grupos.keys()),
                                               default=mis_grupos_nombres)
                
                if st.form_submit_button("Guardar Cambios"):
                    update_data = {
                        "rol": new_rol,
                        "activo": new_activo,
                        "grupo_ids": [opciones_grupos[name] for name in selected_grupos]
                    }
                    if service.actualizar_usuario(u["id"], update_data):
                        st.success("Usuario actualizado")
                        st.rerun()
            
            # Botón de eliminación destructiva
            btn_del = st.button(
                f"🗑️ Eliminar permanentemente a {u['nombre']}", key=f"del_u_{u['id']}"
            )
            if btn_del and service.eliminar_usuario(u["id"]):
                st.rerun()

    # --- TAB 3: CONFIGURACIÓN DE GRUPOS ---
    with tab_groups:
        st.subheader("Estructura de Grupos")
        
        # Crear nuevo grupo
        with st.expander("➕ Crear Nuevo Grupo"), st.form("nuevo_grupo"):
            n_nombre = st.text_input("Nombre del Grupo")
            n_min = st.number_input("Mínimo de presentes (RN3/RN4)", min_value=0, value=2)
            if st.form_submit_button("Crear") and service.crear_grupo(n_nombre, n_min):
                st.success("Grupo creado")
                st.rerun()

        st.divider()
        
        # Listar y editar grupos existentes
        for g in grupos:
            with st.container(border=True):
                c1, c2, c3 = st.columns([2, 1, 1])
                with c1:
                    st.write(f"🏗️ **{g['nombre']}**")
                with c2:
                    new_min = st.number_input("Min. Presentes", value=g["min_presentes"], 
                                            key=f"min_{g['id']}")
                with c3:
                    st.write("") # Spacer
                    if st.button("Actualizar", key=f"upd_g_{g['id']}") \
                       and service.actualizar_grupo(g["id"], {"min_presentes": new_min}):
                        st.success("Actualizado")
                        st.rerun()

    # --- TAB 4: CONFIGURACIÓN GLOBAL ---
    with tab_config:
        st.subheader("⚙️ Configuración del Sistema")
        config = service.obtener_configuracion()

        with st.form("form_config"):
            mostrar_tooltip = st.toggle(
                "Mostrar grupos ausentes en tooltip del calendario",
                value=config.get("mostrar_grupos_tooltip", True),
                help="Cuando está activo, al pasar el cursor sobre una fecha ocupada "
                     "se muestran los grupos con ausencias (sin revelar nombres).",
            )
            if st.form_submit_button("Guardar Configuración"):
                if service.actualizar_configuracion({"mostrar_grupos_tooltip": mostrar_tooltip}):
                    st.success("Configuración guardada")
                    st.rerun()
                else:
                    st.error("Error al guardar la configuración")

if __name__ == "__main__":
    show()
