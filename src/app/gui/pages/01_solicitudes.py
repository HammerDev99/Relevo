from datetime import date, timedelta

import streamlit as st

from app.gui import session_keys
from app.gui.services.solicitud_service import SolicitudService


def show() -> None:
    st.title("📑 Mis Solicitudes")
    
    # SPEC-S15-C7: CSS mejorado para diseño móvil responsivo
    st.markdown("""
        <style>
        /* Forzar columnas a apilarse en móviles */
        @media (max-width: 768px) {
            [data-testid="stHorizontalBlock"] > div {
                flex-direction: column !important;
                width: 100% !important;
            }
            
            /* Ajustar ancho de elementos en móvil */
            [data-testid="stColumn"] {
                width: 100% !important;
                margin-bottom: 1rem !important;
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
        
        /* Mejorar legibilidad de tarjetas */
        .stActionButton { margin-top: 10px; }
        
        /* Ajustar tamaño de botones en móvil */
        @media (max-width: 768px) {
            .stButton > button {
                width: 100% !important;
                padding: 0.75rem !important;
                font-size: 1rem !important;
            }
        }
        </style>
    """, unsafe_allow_html=True)

    service = SolicitudService()
    auth = service.auth
    
    # Obtener info del usuario actual para filtrar backup
    me = auth.get_me()
    mis_grupos = me.get("grupo_ids", []) if me else []
    
    # SPEC-S15-C6: Leer fecha pre-seleccionada desde el calendario
    fecha_presel_str = st.session_state.pop("fecha_preseleccionada", None)
    fecha_presel = date.fromisoformat(fecha_presel_str) if fecha_presel_str else None
    expander_abierto = fecha_presel is not None

    if fecha_presel:
        st.info(f"📌 Fecha pre-seleccionada desde el calendario: **{fecha_presel_str}**")

    # --- Formulario de Nueva Solicitud (S14-C3: Sin st.form para permitir reactividad) ---
    with st.expander("➕ Nueva Solicitud", expanded=expander_abierto):
        tipo = st.selectbox("Tipo de Ausencia", ["vacaciones", "permiso"])

        st.caption(
            "📅 Sugerencia: Configure su navegador en Español (Colombia) "
            "para ver el calendario iniciando en Domingo."
        )

        col1, col2 = st.columns(2)
        with col1:
            f_inicio = st.date_input(
                "Fecha Inicio",
                value=fecha_presel if fecha_presel else date.today(),
                min_value=date.today(),
            )
        
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
        # SPEC-S15-C3: Justificación opcional para todos los tipos de solicitud
        justificacion = st.text_area(
            "Justificación / Motivo (Opcional)",
            help="Puede dejar este campo vacío si lo desea"
        )

        if st.button("Enviar Solicitud", type="primary"):
            if not respaldo_nombre:
                st.error("Debes seleccionar un compañero de respaldo")
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
