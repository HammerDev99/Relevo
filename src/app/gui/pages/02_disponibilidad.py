import calendar
from datetime import date

import streamlit as st

from app.gui.services.coordinacion_service import CoordinacionService
from app.gui.services.disponibilidad_service import DisponibilidadService


def show() -> None:
    st.title("📅 Calendario de Disponibilidad")
    st.info("Consulta los cupos disponibles para planificar tus ausencias. "
            "Garantizamos tu privacidad: no se muestran nombres ni motivos.")

    # SPEC-S15-C7: CSS responsivo
    st.markdown("""
        <style>
        @media (max-width: 768px) {
            [data-testid="stHorizontalBlock"] > div {
                flex-direction: column !important;
                width: 100% !important;
            }
            .stSelectbox { width: 100% !important; }
            .css-1d391kg { padding: 0.5rem !important; }
        }
        @media (min-width: 769px) and (max-width: 1024px) {
            [data-testid="stHorizontalBlock"] > div { padding: 0.5rem !important; }
        }
        </style>
    """, unsafe_allow_html=True)

    service = DisponibilidadService()

    # SPEC-S15-C5: Leer configuración (sin auth, endpoint público)
    config_service = CoordinacionService()
    config = config_service.obtener_configuracion()
    mostrar_tooltip = config.get("mostrar_grupos_tooltip", True)

    # --- Selectores de Mes y Año ---
    hoy = date.today()
    col_y, col_m = st.columns(2)
    with col_y:
        anio = st.number_input("Año", min_value=2024, max_value=2030, value=hoy.year)
    with col_m:
        meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                 "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        mes_nombre = st.selectbox("Mes", options=meses, index=hoy.month - 1)
        mes_index = meses.index(mes_nombre) + 1

    # --- Leyenda ---
    st.markdown("""
        <div style="display: flex; gap: 20px; margin-bottom: 20px; flex-wrap: wrap;">
            <div style="display: flex; align-items: center; gap: 5px;">
                <div style="width: 15px; height: 15px; background-color: #28a745;
                            border-radius: 3px;"></div>
                <span>Disponible</span>
            </div>
            <div style="display: flex; align-items: center; gap: 5px;">
                <div style="width: 15px; height: 15px; background-color: #ffd700;
                            border-radius: 3px;"></div>
                <span>Ocupado (requiere excepción)</span>
            </div>
            <div style="display: flex; align-items: center; gap: 5px;">
                <div style="width: 15px; height: 15px; background-color: #dc3545;
                            border-radius: 3px;"></div>
                <span>Cupo Lleno</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # --- Obtener Datos ---
    datos = service.consultar(anio, mes_index)

    if not datos:
        st.warning("No se pudieron cargar los datos de disponibilidad.")
        return

    # SPEC-S15-C4: mapa fecha → dato completo
    mapa_datos: dict[str, dict] = {d["fecha"]: d for d in datos}

    # --- Renderizar Calendario ---
    # SPEC-S15-C2: Inicio en Domingo
    dias_semana = ["Dom", "Lun", "Mar", "Mié", "Jue", "Vie", "Sáb"]
    cols = st.columns(7)
    for i, dia in enumerate(dias_semana):
        cols[i].markdown(f"**{dia}**")

    primer_dia_semana, num_dias = calendar.monthrange(anio, mes_index)
    offset_domingo = (primer_dia_semana + 1) % 7

    total_slots = num_dias + offset_domingo
    filas = total_slots // 7 + (1 if total_slots % 7 != 0 else 0)

    current_day = 1
    for f in range(filas):
        cols = st.columns(7)
        for d in range(7):
            idx = f * 7 + d
            if offset_domingo <= idx < (offset_domingo + num_dias):
                fecha_str = date(anio, mes_index, current_day).isoformat()
                dato = mapa_datos.get(
                    fecha_str,
                    {"estado": "DISPONIBLE", "razon": None, "grupos_ausentes": []},
                )
                estado = dato["estado"]
                razon = dato.get("razon")
                grupos = dato.get("grupos_ausentes", [])

                # SPEC-S15-C4: festivos/fines de semana en gris
                if razon in ["Festivo", "Fin de semana"]:
                    bg_color = "#e9ecef"
                    txt_color = "#6c757d"
                else:
                    if estado == "DISPONIBLE":
                        bg_color = "#28a745"
                    elif estado == "OCUPADO":
                        bg_color = "#ffd700"
                    else:
                        bg_color = "#dc3545"
                    txt_color = "white" if estado != "OCUPADO" else "black"

                # SPEC-S15-C5: tooltip con grupos ausentes (si config activa)
                titulo = ""
                if mostrar_tooltip and grupos and razon not in ["Festivo", "Fin de semana"]:
                    grupos_str = ", ".join(grupos)
                    titulo = f"Grupos con ausencias: {grupos_str}"
                elif razon:
                    titulo = razon

                with cols[d]:
                    st.markdown(
                        f"""<div style="
                            background-color:{bg_color};color:{txt_color};
                            padding:8px;text-align:center;border-radius:5px;
                            margin:1px;font-weight:bold;border:1px solid #ddd;
                            font-size:0.9rem;" title="{titulo}">{current_day}
                        </div>""",
                        unsafe_allow_html=True,
                    )
                    # SPEC-S15-C6: botón de selección (deshabilitado visualmente, lógica preservada)
                    # _es_habil = razon not in ["Festivo", "Fin de semana"]
                    # if _es_habil and st.button(
                    #     "→",
                    #     key=f"sel_{fecha_str}",
                    #     help=titulo if titulo else f"Seleccionar {fecha_str}",
                    #     use_container_width=True,
                    # ):
                    #         st.session_state["fecha_preseleccionada"] = fecha_str
                    #         st.session_state["detalle_fecha"] = {
                    #             "fecha": fecha_str,
                    #             "estado": estado,
                    #             "grupos": grupos,
                    #         }

                current_day += 1
            else:
                cols[d].empty()

    # SPEC-S15-C6: Panel de detalle al seleccionar una fecha
    detalle = st.session_state.get("detalle_fecha")
    if detalle:
        st.divider()
        fecha_sel = detalle["fecha"]
        estado_sel = detalle["estado"]
        grupos_sel = detalle.get("grupos", [])

        color_map = {"DISPONIBLE": "green", "OCUPADO": "orange", "EXCEPCIONAL": "red"}
        color = color_map.get(estado_sel, "gray")

        st.markdown(f"### 📌 {fecha_sel}")
        st.markdown(f"**Estado:** :{color}[{estado_sel}]")

        if grupos_sel and mostrar_tooltip:
            st.markdown(f"**Grupos con ausencias:** {', '.join(grupos_sel)}")
        elif not grupos_sel:
            st.markdown("**Sin ausencias registradas** — cupo libre.")

        col_btn, col_clear = st.columns([2, 1])
        with col_btn:
            if st.button("📝 Crear Solicitud para este día", type="primary"):
                st.switch_page("pages/01_solicitudes.py")
        with col_clear:
            if st.button("✕ Limpiar selección"):
                del st.session_state["detalle_fecha"]
                if "fecha_preseleccionada" in st.session_state:
                    del st.session_state["fecha_preseleccionada"]
                st.rerun()


if __name__ == "__main__":
    show()
