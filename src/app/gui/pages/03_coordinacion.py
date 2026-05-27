import streamlit as st

from app.gui.services.coordinacion_service import CoordinacionService


def show() -> None:
    st.title("🛡️ Panel de Coordinación")
    st.subheader("Gestión de Solicitudes Pendientes")
    
    service = CoordinacionService()
    pendientes = service.listar_pendientes()
    
    if not pendientes:
        st.success("No hay solicitudes pendientes de procesar. ¡Buen trabajo!")
        return

    for s in pendientes:
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"👤 **Empleado:** {s['empleado_nombre']}")
                st.write(
                    f"Tipo: `{s['tipo'].upper()}` | "
                    f"📅 {s['fecha_inicio']} al {s['fecha_fin']}"
                )
                st.write(
                    f"⏱️ {s['dias_habiles']} días hábiles | "
                    f"🤝 Respaldo: {s['respaldo_nombre']}"
                )
                
                if s["es_excepcion"]:
                    st.warning("⚠️ **TRÁMITE DE EXCEPCIÓN**")
                
                if s["justificacion"]:
                    with st.expander("Ver Justificación"):
                        st.write(s["justificacion"])
            
            with col2:
                st.write("") # Espaciador
                if st.button("✅ Aprobar", key=f"aprov_{s['id']}", use_container_width=True):
                    if service.procesar(s["id"], "aprobada"):
                        st.rerun()

                if st.button("❌ Rechazar", key=f"rech_{s['id']}", use_container_width=True):
                    if service.procesar(s["id"], "rechazada"):
                        st.rerun()

if __name__ == "__main__":
    show()
