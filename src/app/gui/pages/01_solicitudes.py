from datetime import date

import streamlit as st

from app.gui import session_keys
from app.gui.services.solicitud_service import SolicitudService


def show() -> None:
    st.title("📑 Mis Solicitudes")
    service = SolicitudService()
    
    # --- Formulario de Nueva Solicitud ---
    with st.expander("➕ Nueva Solicitud", expanded=False), st.form("nueva_solicitud"):
        tipo = st.selectbox("Tipo de Ausencia", ["vacaciones", "permiso"])
        col1, col2 = st.columns(2)
        with col1:
            f_inicio = st.date_input("Fecha Inicio", min_value=date.today())
        with col2:
            f_fin = st.date_input("Fecha Fin", min_value=f_inicio)
        
        usuarios = service.listar_empleados()
        mi_email = st.session_state.get(session_keys.USER_EMAIL)
        opciones_respaldo = {u["nombre"]: u["id"] for u in usuarios if u["correo"] != mi_email}
        
        respaldo_nombre = st.selectbox(
            "Compañero de Respaldo (RN6)", 
            options=list(opciones_respaldo.keys())
        )
        
        es_excepcion = st.checkbox("¿Tramitar como excepción? (RN4)")
        justificacion = st.text_area(
            "Justificación", 
            help="Obligatorio para permisos o excepciones"
        )
        
        submit = st.form_submit_button("Enviar Solicitud")
        
        if submit:
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
                    st.success("Solicitud enviada correctamente")
                    st.rerun()
                else:
                    st.error(f"Error: {res['error']}")

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
                    st.write(f"⏱️ {s['dias_habiles']} días hábiles")
                with c3:
                    html_badge = (
                        f"<div style='text-align:center; padding:5px; border-radius:5px; "
                        f"background-color:{color}; color:white;'>{s['estado'].upper()}</div>"
                    )
                    st.markdown(html_badge, unsafe_allow_html=True)
                    if s["es_excepcion"]:
                        st.caption("⚠️ Excepción")

if __name__ == "__main__":
    show()
