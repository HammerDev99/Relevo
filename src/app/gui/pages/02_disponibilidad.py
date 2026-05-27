import calendar
from datetime import date

import streamlit as st

from app.gui.services.disponibilidad_service import DisponibilidadService


def show() -> None:
    st.title("📅 Calendario de Disponibilidad")
    st.info("Consulta los cupos disponibles para planificar tus ausencias. "
            "Garantizamos tu privacidad: no se muestran nombres ni motivos.")
    
    service = DisponibilidadService()
    
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
        <div style="display: flex; gap: 20px; margin-bottom: 20px;">
            <div style="display: flex; align-items: center; gap: 5px;">
                <div style="width: 15px; height: 15px; background-color: #28a745; 
                            border-radius: 3px;"></div>
                <span>Disponible (Cupo libre)</span>
            </div>
            <div style="display: flex; align-items: center; gap: 5px;">
                <div style="width: 15px; height: 15px; background-color: #ffd700; 
                            border-radius: 3px;"></div>
                <span>Ocupado (Requiere excepción)</span>
            </div>
            <div style="display: flex; align-items: center; gap: 5px;">
                <div style="width: 15px; height: 15px; background-color: #dc3545; 
                            border-radius: 3px;"></div>
                <span>Cupo Lleno (Excepción agotada)</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # --- Obtener Datos ---
    datos = service.consultar(anio, mes_index)

    if not datos:
        st.warning("No se pudieron cargar los datos de disponibilidad.")
        return

    # SPEC-S15-C4: Crear mapa con información completa (estado + razon)
    mapa_datos = {d["fecha"]: d for d in datos}

    # --- Renderizar Calendario (Grid) ---
    # SPEC-S15-C2: Calendario iniciando en Domingo
    dias_semana = ["Dom", "Lun", "Mar", "Mié", "Jue", "Vie", "Sáb"]
    cols = st.columns(7)
    for i, dia in enumerate(dias_semana):
        cols[i].markdown(f"**{dia}**")

    # Calcular espacios vacíos al inicio del mes
    # calendar.monthrange retorna 0=Lunes, 6=Domingo
    # Para calendario iniciando en Domingo: ajustar offset
    primer_dia_semana, num_dias = calendar.monthrange(anio, mes_index)
    # Convertir de Lunes=0 a Domingo=0
    offset_domingo = (primer_dia_semana + 1) % 7
    
    # Grid de días
    total_slots = num_dias + offset_domingo
    filas = total_slots // 7 + (1 if total_slots % 7 != 0 else 0)

    current_day = 1
    for f in range(filas):
        cols = st.columns(7)
        for d in range(7):
            idx = f * 7 + d
            if offset_domingo <= idx < (offset_domingo + num_dias):
                fecha_str = date(anio, mes_index, current_day).isoformat()
                dato = mapa_datos.get(fecha_str, {"estado": "DISPONIBLE", "razon": None})
                estado = dato["estado"]
                razon = dato.get("razon")

                # SPEC-S15-C4: No pintar festivos ni fines de semana
                # Si es festivo o fin de semana, mostrar en gris sin color de estado
                if razon in ["Festivo", "Fin de semana"]:
                    bg_color = "#e9ecef"
                    txt_color = "#6c757d"
                else:
                    # Colores normales para días hábiles
                    if estado == "DISPONIBLE":
                        bg_color = "#28a745"
                    elif estado == "OCUPADO":
                        bg_color = "#ffd700"
                    else:
                        bg_color = "#dc3545"

                    txt_color = "white" if estado != "OCUPADO" else "black"

                content = f"""
                    <div style="
                        background-color: {bg_color};
                        color: {txt_color};
                        padding: 10px;
                        text-align: center;
                        border-radius: 5px;
                        margin: 2px;
                        font-weight: bold;
                        border: 1px solid #ddd;
                    ">
                        {current_day}
                    </div>
                """
                cols[d].markdown(content, unsafe_allow_html=True)
                current_day += 1
            else:
                cols[d].empty()

if __name__ == "__main__":
    show()
