import streamlit as st
from sqlalchemy import text
from db import engine
import pandas as pd
from datetime import date

# =================================================
# 🧭 CONFIGURACIÓN DEL PANEL
# =================================================
st.set_page_config(page_title="Panel de Ventas", page_icon="💰", layout="wide")
st.title("💰 Panel de Ventas — Administrador")
st.write("Gestión centralizada de ventas por sucursal y fecha.")

# =================================================
# 🔐 VALIDACIÓN DE SESIÓN Y ROL
# =================================================
if "id_usuario" not in st.session_state:
    st.warning("Debes iniciar sesión para acceder.")
    st.stop()

if st.session_state.get("rol") != "admin":
    st.error("⛔ Solo los administradores pueden acceder a este panel.")
    st.stop()

# =================================================
# 🏢 SELECCIÓN DE SUCURSAL
# =================================================
with engine.connect() as conn:
    sucursales = conn.execute(text("""
        SELECT id_sucursal, nombre 
        FROM sucursal 
        WHERE estado = 1 
        ORDER BY nombre ASC
    """)).fetchall()

suc_dict = {s[1]: int(s[0]) for s in sucursales}

st.subheader("🏪 Registrar venta del día")
col1, col2, col3 = st.columns([3, 2, 2])

with col1:
    sucursal_nombre = st.selectbox("Sucursal", list(suc_dict.keys()))
    id_sucursal = suc_dict[sucursal_nombre]

with col2:
    fecha = st.date_input("Fecha", value=date.today())

with col3:
    venta_total = st.number_input("Venta Total (S/.)", min_value=0.0, step=10.0)

# =================================================
# 💾 GUARDAR / ACTUALIZAR VENTA
# =================================================
if st.button("💾 Registrar / Actualizar Venta", use_container_width=True):
    try:
        with engine.begin() as conn:

            existe = conn.execute(text("""
                SELECT consumo 
                FROM registro_insumo
                WHERE fecha = :fecha
                  AND id_sucursal = :sucursal
                  AND id_insumo = 1
            """), {
                "fecha": fecha,
                "sucursal": int(id_sucursal)
            }).fetchone()

            if existe:
                consumo = existe[0] or 0
                ratio_nuevo = consumo / venta_total if venta_total > 0 else 0

                conn.execute(text("""
                    UPDATE registro_insumo
                    SET venta_total = :venta,
                        ratio = :ratio
                    WHERE fecha = :fecha
                      AND id_sucursal = :sucursal
                      AND id_insumo = 1
                """), {
                    "venta": venta_total,
                    "ratio": ratio_nuevo,
                    "fecha": fecha,
                    "sucursal": int(id_sucursal)
                })

                st.success(f"🔄 Venta actualizada correctamente para {sucursal_nombre} — {fecha}")

            else:
                conn.execute(text("""
                    INSERT INTO registro_insumo (id_insumo, id_sucursal, fecha, venta_total)
                    VALUES (1, :sucursal, :fecha, :venta)
                """), {
                    "sucursal": int(id_sucursal),
                    "fecha": fecha,
                    "venta": venta_total
                })

                st.success(f"✅ Venta registrada correctamente para {sucursal_nombre}")

    except Exception as e:
        st.error("❌ Error al registrar la venta.")
        st.exception(e)

# =================================================
# 📊 HISTORIAL DE VENTAS
# =================================================
st.divider()
st.subheader("📊 Historial de Ventas Registradas")

with engine.connect() as conn:
    df = pd.read_sql(text("""
        SELECT 
            r.fecha,
            s.nombre AS sucursal,
            r.venta_total,
            r.id_sucursal
        FROM registro_insumo r
        JOIN sucursal s ON r.id_sucursal = s.id_sucursal
        WHERE r.venta_total IS NOT NULL
        ORDER BY r.fecha DESC
    """), conn)

if df.empty:
    st.info("📭 No hay ventas registradas todavía.")
else:
    df["fecha"] = df["fecha"].astype(str)
    df["id_sucursal"] = df["id_sucursal"].astype(int)

    st.dataframe(
        df[["fecha", "sucursal", "venta_total"]],
        use_container_width=True,
        hide_index=True,
    )

    # =================================================
    # ✏️ EDITAR / ELIMINAR VENTA
    # =================================================
    st.divider()
    st.subheader("✏️ Editar o Eliminar Venta")

    col_f, col_s = st.columns([2, 2])

    with col_f:
        fecha_selec = st.selectbox(
            "Selecciona una fecha",
            sorted(df["fecha"].unique(), reverse=True),
            key="fecha_edit_venta"
        )

    # Convertimos a string para comparar
    fecha_selec_str = str(fecha_selec)

    # Filtrar de forma segura
    df_filtrado = df[df["fecha"] == fecha_selec_str]

    if df_filtrado.empty:
        st.warning("⚠ No se encontró una venta registrada para esa fecha.")
        st.stop()

    venta_row = df_filtrado.iloc[0]

    id_sucursal_edit = int(venta_row["id_sucursal"])
    sucursal_sel = venta_row["sucursal"]
    venta_actual = float(venta_row["venta_total"])

    with col_s:
        st.metric("Sucursal", sucursal_sel)
        st.metric("Venta actual", f"S/. {venta_actual:,.2f}")

    col_edit, col_del = st.columns([1, 1])

    # --------------------
    # ✏️ ACTIVAR EDICIÓN
    # --------------------
    with col_edit:
        if st.button("✏️ Editar Venta"):
            st.session_state.edit_mode = True
            st.session_state.fecha_edit = fecha_selec_str
            st.session_state.sucursal_edit = id_sucursal_edit
            st.session_state.venta_edit = venta_actual

    # --------------------
    # 🗑 ELIMINAR VENTA
    # --------------------
    with col_del:
        if st.button("🗑️ Eliminar Venta"):
            try:
                with engine.begin() as conn:
                    conn.execute(text("""
                        UPDATE registro_insumo
                        SET venta_total = NULL,
                            ratio = 0.0
                        WHERE fecha = :fecha
                          AND id_sucursal = :id_sucursal
                          AND id_insumo = 1
                    """), {
                        "fecha": fecha_selec_str,
                        "id_sucursal": id_sucursal_edit
                    })

                st.success(f"🗑️ Venta eliminada correctamente")
                st.rerun()

            except Exception as e:
                st.error("❌ Error al eliminar la venta.")
                st.exception(e)

    # =================================================
    # FORMULARIO DE EDICIÓN
    # =================================================
    if st.session_state.get("edit_mode", False):
        st.divider()
        st.subheader("📝 Editar Venta")

        nueva_venta = st.number_input(
            "Nuevo monto (S/.)",
            min_value=0.0,
            value=st.session_state.venta_edit,
            step=10.0
        )

        if st.button("💾 Guardar Cambios"):
            try:
                with engine.begin() as conn:

                    consumo = conn.execute(text("""
                        SELECT consumo FROM registro_insumo
                        WHERE fecha = :fecha
                          AND id_sucursal = :sucursal
                          AND id_insumo = 1
                    """), {
                        "fecha": st.session_state.fecha_edit,
                        "sucursal": st.session_state.sucursal_edit
                    }).fetchone()

                    consumo_val = consumo[0] if consumo and consumo[0] else 0
                    ratio_nuevo = consumo_val / nueva_venta if nueva_venta > 0 else 0

                    conn.execute(text("""
                        UPDATE registro_insumo
                        SET venta_total = :venta,
                            ratio = :ratio
                        WHERE fecha = :fecha
                          AND id_sucursal = :sucursal
                          AND id_insumo = 1
                    """), {
                        "venta": nueva_venta,
                        "ratio": ratio_nuevo,
                        "fecha": st.session_state.fecha_edit,
                        "sucursal": st.session_state.sucursal_edit
                    })

                st.success("💾 Venta actualizada correctamente")
                st.session_state.edit_mode = False
                st.rerun()

            except Exception as e:
                st.error("❌ Error al actualizar la venta.")
                st.exception(e)
