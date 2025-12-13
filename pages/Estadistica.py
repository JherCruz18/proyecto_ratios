import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy import text
from db import engine
from datetime import datetime

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Dashboard Carbón", page_icon="📊", layout="wide")

st.title("📊 Dashboard — Ratios del Carbón")

# =========================
# VALIDAR SESIÓN
# =========================
if "id_usuario" not in st.session_state:
    st.warning("Debes iniciar sesión primero")
    st.stop()

id_usuario = st.session_state["id_usuario"]

# =========================
# OBTENER SUCURSAL DEL USUARIO
# =========================
with engine.connect() as conn:
    u = conn.execute(text("""
        SELECT id_sucursal 
        FROM usuario 
        WHERE id_usuario = :id
    """), {"id": id_usuario}).fetchone()

if not u:
    st.error("No tienes sucursal asignada.")
    st.stop()

id_sucursal = u[0]

# =========================
# FILTRO DE FECHAS
# =========================
st.subheader("📅 Seleccionar Rango")

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

if fecha_inicio > fecha_fin:
    st.error("La fecha inicio no puede ser mayor a la final.")
    st.stop()

# =========================
# CONSULTA DE DATOS (SOLO ESTADO = 1)
# =========================
with engine.connect() as conn:
    df = pd.read_sql(text("""
        SELECT
            fecha,
            consumo,
            venta_total,
            ROUND(ratio * 100, 2) AS ratio_pct
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
    st.info("📭 No hay datos en este rango.")
    st.stop()

df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")

# =========================
# MÉTRICAS
# =========================
st.divider()
st.subheader("📌 Resumen General del Rango")

consumo_total = df["consumo"].sum()
venta_total = df["venta_total"].sum()
ratio_prom = df["ratio_pct"].mean()
df["ratio_eval"] = df["ratio_pct"].apply(lambda r: r * 100 if r < 1 else r) 
dias_fuera_meta = len(df[df["ratio_eval"] > 55])
def normalizar_ratio(r):
    return r * 100 if r < 1 else r

df["ratio_eval"] = df["ratio_pct"].apply(normalizar_ratio)

dias_fuera_meta = (df["ratio_eval"] > 55).sum()

colA, colB, colC, colD = st.columns(4)

with colA:
    st.metric("🔥 Consumo Total (kg)", round(consumo_total, 2))

with colB:
    st.metric("💰 Venta Total (S/.)", round(venta_total, 2))

with colC:
    st.metric("📊 Ratio Promedio (%)", f"{round(ratio_prom, 2)}%")

with colD:
    st.metric("⚠️ Días fuera de meta (>55%)", dias_fuera_meta)

# =========================
# GRAFICO 1 — RATIO POR DÍA (con etiquetas y todas las fechas)
# =========================
st.divider()
st.subheader("📈 Evolución del Ratio (%) por Día")

# Convertir fechas a string para mostrarlas todas sin que Matplotlib las auto-oculte
df["fecha_str"] = df["fecha"].dt.strftime("%d/%m/%Y")

fig, ax = plt.subplots(figsize=(14, 4))

# Gráfico
ax.plot(df["fecha_str"], df["ratio_pct"], marker="o", label="Ratio diario")

# Etiquetas de datos sobre cada punto
for x, y in zip(df["fecha_str"], df["ratio_pct"]):
    ax.text(x, y, f"{y}%", fontsize=9, ha="center", va="bottom")

# Forzar a mostrar todas las fechas en el eje X
ax.set_xticks(df["fecha_str"])
ax.set_xticklabels(df["fecha_str"], rotation=45, ha="right")

ax.set_ylabel("Ratio (%)")
ax.grid(True)
ax.legend()

st.pyplot(fig)


# =========================
# TABLA RESUMEN (FORMATO ESPAÑOL)
# =========================
st.subheader("📋 Tabla Resumen")

df_display = df.copy()
df_display["fecha"] = df_display["fecha"].dt.strftime("%d/%m/%Y")

st.dataframe(df_display, use_container_width=True, hide_index=True)
