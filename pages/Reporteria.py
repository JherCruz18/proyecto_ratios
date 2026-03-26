import streamlit as st
from datetime import datetime
from reporteria_extract import exportar_carbon_excel

st.set_page_config(page_title="📊 Reportería", layout="wide")

# =========================
# VALIDAR SESIÓN
# =========================
if "id_usuario" not in st.session_state:
    st.warning("Debes iniciar sesión")
    st.stop()

id_sucursal = st.session_state["id_sucursal"]
nombre_sucursal = st.session_state["nombre_sucursal"]

st.title("📊 Reporte de Carbón")
st.caption(f"🏢 {nombre_sucursal}")

# =========================
# FILTROS
# =========================
c1, c2 = st.columns(2)
with c1:
    fecha_inicio = st.date_input("Fecha inicio", value=datetime.now().replace(day=1))
with c2:
    fecha_fin = st.date_input("Fecha fin", value=datetime.now())

# =========================
# EXPORTAR
# =========================
if st.button("📤 Exportar Excel", use_container_width=True):
    try:
        # Crear timestamp aquí
        timestamp = datetime.now().strftime("%d%m%Y_%H%M")

        # Construir el nombre del archivo
        nombre_archivo = f"Reporte_{nombre_sucursal}_{timestamp}.xlsx"

        ruta = exportar_carbon_excel(
            id_sucursal=id_sucursal,
            nombre_sucursal=nombre_sucursal,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            salida=nombre_archivo
        )

        with open(ruta, "rb") as f:
            st.download_button(
                "⬇️ Descargar archivo",
                f,
                file_name=ruta,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:
        st.error(str(e))
