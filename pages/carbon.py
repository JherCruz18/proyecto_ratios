import streamlit as st
import pandas as pd
from sqlalchemy import text
from db import engine
from datetime import datetime, time

# =========================
# CONFIGURACIÓN DE PÁGINA
# =========================
st.set_page_config(
    page_title="Control de Carbón",
    page_icon="🔥",
    layout="wide"
)

# =========================
# VALIDAR SESIÓN
# =========================
if "id_usuario" not in st.session_state:
    st.warning("Debes iniciar sesión primero")
    st.stop()

id_usuario = st.session_state["id_usuario"]
username = st.session_state.get("username", "Usuario")

# =========================
# OBTENER SUCURSAL
# =========================
with engine.connect() as conn:
    usuario = conn.execute(text("""
        SELECT u.id_sucursal, s.nombre
        FROM usuario u
        LEFT JOIN sucursal s ON u.id_sucursal = s.id_sucursal
        WHERE u.id_usuario = :id_usuario
    """), {"id_usuario": id_usuario}).fetchone()

if not usuario:
    st.error("Usuario sin sucursal asignada")
    st.stop()

id_sucursal = usuario[0]
nombre_sucursal = usuario[1] if usuario[1] else "Sucursal"

# =========================
# HEADER
# =========================
col_title, col_user = st.columns([4,1])

with col_title:
    st.title("🔥 Control de Carbón")

with col_user:
    st.metric("👤 Usuario", username)

st.caption(f"🏢 {nombre_sucursal}")

# =========================
# BOTÓN NUEVO REGISTRO
# =========================
if st.button("➕ Nuevo Registro"):
    st.session_state.show_modal = True
    st.session_state.pop("selected_id", None)

# =========================
# MODAL NUEVO REGISTRO
# =========================
@st.dialog("📝 Registrar Nuevo Carbón")
def modal_registro():

    fecha = st.date_input("📅 Fecha del Registro")

    with engine.connect() as conn:
        ultimo = conn.execute(text("""
            SELECT stock_final
            FROM registro_insumo
            WHERE id_sucursal = :id_sucursal
              AND id_insumo = 1
              AND estado = 1
            ORDER BY fecha DESC
            LIMIT 1
        """), {"id_sucursal": id_sucursal}).fetchone()

    stock_inicial = float(ultimo[0]) if ultimo else 0.0
    st.info(f"Stock Inicial automático: {stock_inicial} kg")

    ingreso = st.number_input("Ingreso (kg)", min_value=0.0)
    reposicion = st.number_input("Reposición (kg)", min_value=0.0)

    hora_actual = datetime.now().time()
    puede_stock_final = fecha < datetime.now().date() or hora_actual >= time(19, 0)

    if puede_stock_final:
        stock_final = st.number_input("Stock Final (kg)", min_value=0.0)
    else:
        stock_final = 0.0
        st.info("El stock final solo puede ingresarse luego de las 7PM")

    consumo = stock_inicial + ingreso + reposicion - stock_final

    if st.button("💾 Guardar"):
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO registro_insumo(
                    id_insumo, id_sucursal, id_usuario, fecha,
                    stock_inicial, ingreso, consumo, reposicion,
                    stock_final, venta_total, ratio, estado
                )
                VALUES(
                    1, :id_sucursal, :id_usuario, :fecha,
                    :si, :ing, :cons, :rep,
                    :sf, 0, 0, 1
                )
            """), {
                "id_sucursal": id_sucursal,
                "id_usuario": id_usuario,
                "fecha": fecha,
                "si": stock_inicial,
                "ing": ingreso,
                "cons": consumo,
                "rep": reposicion,
                "sf": stock_final
            })

        st.session_state.show_modal = False
        st.rerun()

# =========================
# HISTORIAL
# =========================
st.divider()

col1, col2 = st.columns(2)

with col1:
    fecha_inicio = st.date_input(
        "Fecha inicio",
        value=datetime.now().replace(day=1).date()
    )

with col2:
    fecha_fin = st.date_input(
        "Fecha fin",
        value=datetime.now().date()
    )

with engine.connect() as conn:
    df = pd.read_sql(text("""
        SELECT
            id_registro,
            fecha,
            stock_inicial,
            ingreso,
            consumo,
            reposicion,
            stock_final,
            venta_total,
            ROUND(ratio * 100,2) AS ratio_pct
        FROM registro_insumo
        WHERE id_sucursal = :id_sucursal
          AND id_insumo = 1
          AND estado = 1
          AND fecha BETWEEN :fi AND :ff
        ORDER BY fecha ASC
    """), conn, params={
        "id_sucursal": id_sucursal,
        "fi": fecha_inicio,
        "ff": fecha_fin
    })

if df.empty:
    st.info("No hay registros")
else:

    df["fecha"] = pd.to_datetime(df["fecha"]).dt.date
    df["Fecha"] = df["fecha"].apply(lambda x: x.strftime("%d/%m/%Y"))
    df["Ratio %"] = df["ratio_pct"].apply(lambda x: f"{x:.2f}%")

    event = st.dataframe(
        df[[
            "Fecha",
            "stock_inicial",
            "ingreso",
            "consumo",
            "reposicion",
            "stock_final",
            "venta_total",
            "Ratio %"
        ]],
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row"
    )

    if event.selection and event.selection["rows"]:

        selected_index = event.selection["rows"][0]
        registro_id = int(df.iloc[selected_index]["id_registro"])  # 🔥 FIX AQUÍ

        col1, col2 = st.columns(2)

        with col1:
            if st.button("✏️ Editar Registro"):
                st.session_state.selected_id = registro_id
                st.session_state.show_modal = False

        with col2:
            if st.button("🗑️ Eliminar Registro"):
                with engine.begin() as conn:
                    conn.execute(text("""
                        UPDATE registro_insumo
                        SET estado = 0
                        WHERE id_registro = :id
                    """), {"id": registro_id})
                st.rerun()

# =========================
# MODAL EDITAR
# =========================
@st.dialog("✏️ Editar Registro")
def modal_editar():

    registro_id = int(st.session_state.selected_id)  # 🔥 también aseguramos aquí

    with engine.connect() as conn:
        data = conn.execute(text("""
            SELECT fecha, stock_inicial, ingreso,
                   reposicion, stock_final, venta_total
            FROM registro_insumo
            WHERE id_registro = :id
        """), {"id": registro_id}).fetchone()

    fecha = data[0]

    st.write(f"📅 Editando: {fecha.strftime('%d/%m/%Y')}")

    stock_inicial = st.number_input("Stock Inicial", value=float(data[1]))
    ingreso = st.number_input("Ingreso", value=float(data[2]))
    reposicion = st.number_input("Reposición", value=float(data[3]))
    stock_final = st.number_input("Stock Final", value=float(data[4]))
    venta_total = st.number_input("Venta Total", value=float(data[5]))

    if st.button("💾 Guardar cambios"):

        consumo = stock_inicial + ingreso + reposicion - stock_final
        ratio = consumo / venta_total if venta_total > 0 else 0

        with engine.begin() as conn:
            conn.execute(text("""
                UPDATE registro_insumo
                SET stock_inicial=:si,
                    ingreso=:ing,
                    reposicion=:rep,
                    stock_final=:sf,
                    consumo=:cons,
                    venta_total=:vt,
                    ratio=:rat
                WHERE id_registro=:id
            """), {
                "si": stock_inicial,
                "ing": ingreso,
                "rep": reposicion,
                "sf": stock_final,
                "cons": consumo,
                "vt": venta_total,
                "rat": ratio,
                "id": registro_id
            })

        del st.session_state.selected_id
        st.rerun()

# =========================
# CONTROL DE MODALES
# =========================
if st.session_state.get("show_modal", False):
    modal_registro()

elif "selected_id" in st.session_state:
    modal_editar()

# =========================
# RESUMEN
# =========================
st.divider()
st.markdown("### 📊 Resumen del rango")

if not df.empty:
    consumo_total = df["consumo"].sum()
    venta_total_mes = df["venta_total"].sum()
    ratio_mes = (consumo_total / venta_total_mes) * 100 if venta_total_mes > 0 else 0
else:
    ratio_mes = 0

meta_pct = 42

if ratio_mes > meta_pct:
    color = "#ff6b6b"; estado = "⚠️ Ratio Excesivo"
elif ratio_mes < 42:
    color = "#51cf66"; estado = "✅ Ratio Controlado"
else:
    color = "#ff8c00"; estado = "⚡ Ratio Estable"

c1, c2 = st.columns([2, 1])

with c1:
    st.markdown(f"""
    <div style="background:{color}; padding:20px; border-radius:10px; text-align:center;">
        <h3 style="color:white;">Ratio (Rango)</h3>
        <h1 style="color:white;">{round(ratio_mes,2)}%</h1>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div style="background:{color}; padding:20px; border-radius:10px; text-align:center;">
        <h3 style="color:white;">{estado}</h3>
    </div>
    """, unsafe_allow_html=True)