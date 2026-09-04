import calendar
import html
from datetime import date
from typing import Any

import streamlit as st

from app.gui import session_keys
from app.gui.services.coordinacion_service import CoordinacionService
from app.gui.services.disponibilidad_service import DisponibilidadService


@st.cache_data(ttl=300, show_spinner=False)
def _cargar_configuracion() -> dict[str, Any]:
    """SPEC-S18-E1: la configuración global cambia rara vez; se cachea 5 min.

    Sin esto, cada clic en la navegación de mes disparaba una petición HTTP
    extra, lo que en móvil sobre la red judicial se percibe como lentitud.
    """
    return CoordinacionService().obtener_configuracion()


@st.cache_data(ttl=60, show_spinner=False)
def _cargar_disponibilidad(anio: int, mes: int, usuario_id: int | None) -> list[dict[str, Any]]:
    """SPEC-S18-E1: cachea el mes consultado; navegar atrás no repite la petición.

    `usuario_id` entra en la clave de caché porque la respuesta depende de la
    sesión (RN5: nombres y `estado_grupo_propio` varían según el usuario).
    """
    return DisponibilidadService().consultar(anio, mes)


def _construir_detalle(dato: dict[str, Any], mostrar_tooltip: bool) -> str:
    """Texto informativo de un día (SPEC-S15-C5, S18-A2, S18-D1).

    Se usa tanto en el `title=` del calendario (hover, escritorio) como en el
    listado táctil de SPEC-S18-E2, para no duplicar la lógica.
    """
    razon = dato.get("razon")
    if razon in ["Festivo", "Fin de semana"]:
        return str(razon)

    partes = []
    if dato.get("empleados_ausentes"):
        partes.append(f"Ausentes: {', '.join(dato['empleados_ausentes'])}")
    if mostrar_tooltip and dato.get("grupos_ausentes"):
        partes.append(f"Grupos con ausencias: {', '.join(dato['grupos_ausentes'])}")
    # SPEC-S18-D1: avisar si el cupo propio sigue libre aunque el día aparezca
    # ocupado por saturación de otro grupo.
    estado_propio = dato.get("estado_grupo_propio")
    if estado_propio and estado_propio != dato.get("estado"):
        partes.append(f"Tu grupo: {estado_propio}")

    return " | ".join(partes) or (razon or "")


def show() -> None:
    st.title("📅 Disponibilidad")

    st.markdown("""
    <style>
    /* ── Botones de navegación mes/año: estilo neutro ── */
    [data-testid="stBaseButton-secondary"] {
        background-color: #f0f2f6 !important;
        color: #444 !important;
        border: 1px solid #d0d3da !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
    }
    [data-testid="stBaseButton-secondary"]:hover {
        background-color: #e0e3ea !important;
        border-color: #b0b3ba !important;
    }
    @media (max-width: 768px) {
        .stSelectbox, .stNumberInput { width: 100% !important; }
    }

    /* ── Cabecera días de la semana ── */
    .cal-header {
        display: grid;
        grid-template-columns: repeat(7, 1fr);
        gap: 2px;
        margin-bottom: 2px;
    }
    .cal-header-cell {
        text-align: center;
        font-weight: 700;
        font-size: 0.75rem;
        color: #555;
        padding: 4px 0;
        background: #f0f2f6;
        border-radius: 4px;
    }

    /* ── Grid del calendario ── */
    .cal-grid {
        display: grid;
        grid-template-columns: repeat(7, 1fr);
        gap: 3px;
    }
    .cal-cell {
        text-align: center;
        border-radius: 6px;
        border: 1px solid #ddd;
        font-weight: 700;
        cursor: default;
        line-height: 1;
        /* Tamaño base (desktop) */
        padding: 10px 4px;
        font-size: 0.95rem;
        min-height: 40px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    @media (max-width: 480px) {
        .cal-cell {
            padding: 8px 2px;
            font-size: 0.8rem;
            min-height: 36px;
            border-radius: 4px;
        }
        .cal-header-cell {
            font-size: 0.65rem;
            padding: 3px 0;
        }
        /* Título más compacto en móvil */
        h1 { font-size: 1.3rem !important; }
    }
    @media (min-width: 481px) and (max-width: 768px) {
        .cal-cell {
            padding: 10px 3px;
            font-size: 0.85rem;
            min-height: 38px;
        }
    }

    /* ── Leyenda compacta ── */
    .leyenda {
        display: flex;
        flex-wrap: wrap;
        gap: 8px 16px;
        margin: 10px 0 14px;
        font-size: 0.82rem;
    }
    .leyenda-item {
        display: flex;
        align-items: center;
        gap: 5px;
        white-space: nowrap;
    }
    .leyenda-dot {
        width: 12px;
        height: 12px;
        border-radius: 3px;
        flex-shrink: 0;
    }
    </style>
    """, unsafe_allow_html=True)

    config = _cargar_configuracion()
    mostrar_tooltip = config.get("mostrar_grupos_tooltip", True)

    # --- Navegación de Mes y Año con botones ---
    hoy = date.today()
    meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
             "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

    if "cal_anio" not in st.session_state:
        st.session_state.cal_anio = hoy.year
    if "cal_mes" not in st.session_state:
        st.session_state.cal_mes = hoy.month

    col_y1, col_y2, col_y3, col_gap, col_m1, col_m2, col_m3 = st.columns([1, 2, 1, 0.3, 1, 3, 1])

    # Capturar clics ANTES de renderizar labels (evita desfase en primera pulsación)
    with col_y1:
        anio_menos = st.button("−", key="anio_menos", use_container_width=True)
    with col_y3:
        anio_mas = st.button("+", key="anio_mas", use_container_width=True)
    with col_m1:
        mes_ant = st.button("‹", key="mes_ant", use_container_width=True)
    with col_m3:
        mes_sig = st.button("›", key="mes_sig", use_container_width=True)

    # Actualizar estado tras capturar todos los clics
    if anio_menos and st.session_state.cal_anio > 2024:
        st.session_state.cal_anio -= 1
    if anio_mas and st.session_state.cal_anio < 2030:
        st.session_state.cal_anio += 1
    if mes_ant:
        if st.session_state.cal_mes == 1:
            st.session_state.cal_mes = 12
            if st.session_state.cal_anio > 2024:
                st.session_state.cal_anio -= 1
        else:
            st.session_state.cal_mes -= 1
    if mes_sig:
        if st.session_state.cal_mes == 12:
            st.session_state.cal_mes = 1
            if st.session_state.cal_anio < 2030:
                st.session_state.cal_anio += 1
        else:
            st.session_state.cal_mes += 1

    # Renderizar labels con estado ya actualizado
    label_style = "text-align:center;font-weight:700;padding:6px 0;font-size:1rem;"
    with col_y2:
        st.markdown(
            f"<div style='{label_style}'>{st.session_state.cal_anio}</div>",
            unsafe_allow_html=True,
        )
    with col_m2:
        st.markdown(
            f"<div style='{label_style}'>{meses[st.session_state.cal_mes - 1]}</div>",
            unsafe_allow_html=True,
        )

    anio = st.session_state.cal_anio
    mes_index = st.session_state.cal_mes

    # --- Leyenda compacta ---
    st.markdown("""
    <div class="leyenda">
        <div class="leyenda-item">
            <div class="leyenda-dot" style="background:#28a745;"></div><span>Disponible</span>
        </div>
        <div class="leyenda-item">
            <div class="leyenda-dot" style="background:#ffd700;"></div><span>Ocupado</span>
        </div>
        <div class="leyenda-item">
            <div class="leyenda-dot" style="background:#dc3545;"></div><span>Cupo lleno</span>
        </div>
        <div class="leyenda-item">
            <div class="leyenda-dot" style="background:#e9ecef;border:1px solid #ccc;"></div>
            <span>No hábil</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- Obtener Datos ---
    datos = _cargar_disponibilidad(
        anio, mes_index, st.session_state.get(session_keys.USER_ID)
    )
    if not datos:
        st.warning("No se pudieron cargar los datos de disponibilidad.")
        return

    mapa_datos: dict[str, dict[str, Any]] = {d["fecha"]: d for d in datos}

    # --- Cabecera días (SPEC-S15-C2: inicia en Domingo) ---
    dias_semana = ["Dom", "Lun", "Mar", "Mié", "Jue", "Vie", "Sáb"]
    cabecera_html = "".join(
        f'<div class="cal-header-cell">{d}</div>' for d in dias_semana
    )
    st.markdown(f'<div class="cal-header">{cabecera_html}</div>', unsafe_allow_html=True)

    # --- Grid del calendario como HTML puro ---
    primer_dia_semana, num_dias = calendar.monthrange(anio, mes_index)
    offset_domingo = (primer_dia_semana + 1) % 7

    celdas_html = ""
    # SPEC-S18-E2: se acumulan para el listado táctil (en móvil no hay hover)
    detalles_mes: list[tuple[int, str, str]] = []

    # Celdas vacías al inicio
    for _ in range(offset_domingo):
        celdas_html += '<div class="cal-cell" style="background:#fff;border-color:transparent;">'
        celdas_html += "</div>"

    for dia in range(1, num_dias + 1):
        fecha_str = date(anio, mes_index, dia).isoformat()
        dato = mapa_datos.get(
            fecha_str,
            {
                "estado": "DISPONIBLE",
                "razon": None,
                "grupos_ausentes": [],
                "empleados_ausentes": [],
                "estado_grupo_propio": None,
            },
        )
        estado = dato["estado"]
        razon = dato.get("razon")

        # SPEC-S15-C4: festivos / fines de semana en gris
        if razon in ["Festivo", "Fin de semana"]:
            bg, fg = "#e9ecef", "#999"
        elif estado == "DISPONIBLE":
            bg, fg = "#28a745", "white"
        elif estado == "OCUPADO":
            bg, fg = "#ffd700", "#333"
        else:
            bg, fg = "#dc3545", "white"

        titulo = _construir_detalle(dato, mostrar_tooltip)
        if titulo and razon not in ["Festivo", "Fin de semana"]:
            detalles_mes.append((dia, estado, titulo))

        # El tooltip se inyecta con unsafe_allow_html: escapar el contenido
        tooltip = f' title="{html.escape(titulo, quote=True)}"' if titulo else ""
        celdas_html += (
            f'<div class="cal-cell" style="background:{bg};color:{fg};"'
            f"{tooltip}>{dia}</div>"
        )

    st.markdown(f'<div class="cal-grid">{celdas_html}</div>', unsafe_allow_html=True)

    # SPEC-S18-E2: los dispositivos táctiles no disparan :hover, por lo que el
    # atributo title= del calendario es inaccesible en móvil. Este listado
    # expone la misma información sin depender del puntero.
    if detalles_mes:
        icono = {"DISPONIBLE": "🟢", "OCUPADO": "🟡", "EXCEPCIONAL": "🔴"}
        with st.expander(f"📋 Detalle de días con ausencias ({len(detalles_mes)})"):
            for dia_num, estado_dia, texto in detalles_mes:
                st.markdown(
                    f"**{icono.get(estado_dia, '•')} {dia_num} de "
                    f"{meses[mes_index - 1]}** — {texto}"
                )

    # SPEC-S15-C6: Panel de detalle (lógica preservada, activable con botones cuando se reactive)
    detalle = st.session_state.get("detalle_fecha")
    if detalle:
        st.divider()
        estado_sel = detalle["estado"]
        grupos_sel = detalle.get("grupos", [])
        color_map = {"DISPONIBLE": "green", "OCUPADO": "orange", "EXCEPCIONAL": "red"}
        color = color_map.get(estado_sel, "gray")
        st.markdown(f"### 📌 {detalle['fecha']}")
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
            if st.button("✕ Limpiar"):
                for k in ["detalle_fecha", "fecha_preseleccionada"]:
                    st.session_state.pop(k, None)
                st.rerun()


if __name__ == "__main__":
    show()
