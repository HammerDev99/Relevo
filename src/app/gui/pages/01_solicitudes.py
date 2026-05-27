from datetime import date, timedelta

import streamlit as st

from app.gui import session_keys
from app.gui.services.solicitud_service import SolicitudService


def show() -> None:
    st.title("📑 Mis Solicitudes")
    
    # S14-C3: Req 3 - Inyectar CSS para diseño móvil responsivo
    st.markdown("""
        <style>
        /* Forzar columnas a apilarse en móviles */
        @media (max-width: 640px) {
            [data-testid="stHorizontalBlock"] {
                flex-direction: column !important;
            }
        }
        /* Mejorar legibilidad de tarjetas */
        .stActionButton { margin-top: 10px; }
        </style>
    """, unsafe_allow_html=True)

    service = SolicitudService()
    auth = service.auth
    
    # Obtener info del usuario actual para filtrar backup
    me = auth.get_me()
    mis_grupos = me.get("grupo_ids", []) if me else []
    
    # --- Formulario de Nueva Solicitud (S14-C3: Sin st.form para permitir reactividad) ---
    with st.expander("➕ Nueva Solicitud", expanded=False):
        tipo = st.selectbox("Tipo de Ausencia", ["vacaciones", "permiso"])
        
        st.caption(
            "📅 Sugerencia: Configure su navegador en Español (Colombia) "
            "para ver el calendario iniciando en Domingo."
        )
        
        col1, col2 = st.columns(2)
        with col1:
            f_inicio = st.date_input("Fecha Inicio", min_value=date.today())
        
        with col2:
            if tipo == "vacaciones":
                # S14-C3: Req 8 - Cálculo automático de 22 días calendario
                f_fin_calc = f_inicio + timedelta(days=21)
                st.info(f"Fecha Fin estimada: **{f_fin_calc.isoformat()}**")
                st.caption("(22 días calendario proyectados)")
                f_fin = f_fin_calc
            else:
                # S14-C3: Req 6 - Por defecto el mismo día para permisos
                f_fin = st.date_input("Fecha Fin", value=f_inicio, min_value=f_inicio)
        
        usuarios = service.listar_empleados()
        mi_email = st.session_state.get(session_keys.USER_EMAIL)
        
        # S13-C3: Filtrar automáticamente por miembros del mismo grupo
        opciones_respaldo = {
            u["nombre"]: u["id"] 
            for u in usuarios 
            if u["correo"] != mi_email and any(gid in mis_grupos for gid in u.get("grupo_ids", []))
        }
        
        if not opciones_respaldo:
            st.warning("⚠️ No se encontraron compañeros en sus mismos grupos para el respaldo.")
            # Fallback a todos los usuarios si no hay nadie en el grupo (seguridad)
            opciones_respaldo = {u["nombre"]: u["id"] for u in usuarios if u["correo"] != mi_email}

        respaldo_nombre = st.selectbox(
            "Compañero de Respaldo (Mismo Grupo)", 
            options=list(opciones_respaldo.keys())
        )
        
        es_excepcion = st.checkbox("¿Tramitar como excepción? (RN4)")
        justificacion = st.text_area(
            "Justificación / Motivo", 
            help="Obligatorio para permisos o excepciones"
        )
        
        if st.button("Enviar Solicitud", type="primary"):
            if not respaldo_nombre:
                st.error("Debes seleccionar un compañero de respaldo")
            elif tipo == "permiso" and not justificacion:
                st.error("Los permisos requieren justificación")
            else:
                data = {
                    "tipo": tipo,
                    "fecha_inicio": f_inicio.isoformat(),
                    "fecha_fin": f_fin.isoformat(),
                    "respaldo_id": opciones_respaldo[respaldo_nombre],
                    "es_excepcion": es_excepcion,
                    "justificacion": justificacion
                }
                res = service.crear(data)
                if res["success"]:
                    st.success("Solicitud procesada correctamente (Autogestión)")
                    st.rerun()
                else:
                    err_msg = res['error']
                    if "CUPO_LLENO" in err_msg:
                        st.warning(f"⚠️ {err_msg}")
                        st.info("💡 Puede intentar guardarla marcando la casilla "
                                "'¿Tramitar como excepción?'")
                    else:
                        st.error(f"Error: {err_msg}")

    st.divider()

    # --- Listado de Solicitudes ---
    st.subheader("Historial de Solicitudes")
    solicitudes = service.listar_propias()
    
    if not solicitudes:
        st.info("Aún no tienes solicitudes registradas.")
    else:
        for s in reversed(solicitudes):
            # Lógica de colores simplificada
            if s["estado"] == "pendiente":
                color = "#ffd700"
            elif s["estado"] == "aprobada":
                color = "#28a745"
            else:
                color = "#dc3545"

            with st.container(border=True):
                c1, c2, c3 = st.columns([2, 2, 1])
                with c1:
                    st.write(f"**{s['tipo'].upper()}**")
                    st.caption(f"Creada el: {s['creada_en'][:10]}")
                with c2:
                    st.write(f"📅 {s['fecha_inicio']} al {s['fecha_fin']}")
                    label_dias = "días calendario" if s["tipo"] == "vacaciones" else "días hábiles"
                    st.write(f"⏱️ {s['dias_habiles']} {label_dias}")
                with c3:
                    html_badge = (
                        f"<div style='text-align:center; padding:5px; border-radius:5px; "
                        f"background-color:{color}; color:white;'>{s['estado'].upper()}</div>"
                    )
                    st.markdown(html_badge, unsafe_allow_html=True)
                    if s["es_excepcion"]:
                        st.caption("⚠️ Excepción")
                    btn_del = st.button("🗑️ Eliminar", key=f"del_{s['id']}")
                    if btn_del and service.eliminar_propia(s['id']):
                        st.rerun()

if __name__ == "__main__":
    show()
