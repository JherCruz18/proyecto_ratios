import streamlit as st
import pandas as pd
from sqlalchemy import text
from db import engine
from datetime import datetime, time, date

# =========================
# CONFIGURACIÓN DE PÁGINA
# =========================
st.set_page_config(
    page_title="Control de Carbón",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------
# Helper para reiniciar
def safe_rerun():
    if hasattr(st, "experimental_rerun"):
        try:
            st.experimental_rerun()
        except Exception:
            try:
                st.rerun()
            except Exception:
                st.session_state["_tmp_toggle"] = not st.session_state.get("_tmp_toggle", False)
    else:
        if hasattr(st, "rerun"):
            try:
                st.rerun()
            except Exception:
                st.session_state["_tmp_toggle"] = not st.session_state.get("_tmp_toggle", False)
        else:
            st.session_state["_tmp_toggle"] = not st.session_state.get("_tmp_toggle", False)

# =========================
# CSS PERSONALIZADO
# =========================
st.markdown("""
    <style>
    .main { background-color: #1a1a1a; }
    [data-testid="stMetric"] { background: linear-gradient(135deg, #ff8c00 0%, #ff6b35 100%); padding: 12px; border-radius: 8px; color: #fff; }
    [data-testid="stDataFrame"] { background-color: #2a2a2a; color: #fff; }
    </style>
""", unsafe_allow_html=True)

# =========================
# VALIDAR SESIÓN
# =========================
if "id_usuario" not in st.session_state:
    st.warning("Debes iniciar sesión primero")
    st.stop()

id_usuario = st.session_state["id_usuario"]
username = st.session_state.get("username", "Usuario")

# =========================
# OBTENER SUCURSAL DEL USUARIO
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
nombre_sucursal = usuario[1] if usuario[1] else "Sucursal Desconocida"

# =========================
# TITULO
# =========================
col_title, col_user, col_logout = st.columns([3, 1, 1])
with col_title:
    st.title("🔥 Control de Carbón")
with col_user:
    st.metric("👤 Usuario", username)
with col_logout:
    st.markdown("<div style='margin-top:12px'></div>", unsafe_allow_html=True)
    if st.button("🔒 Cerrar Sesión", use_container_width=True):
        st.session_state.clear()
        safe_rerun()
st.caption(f"🏢 {nombre_sucursal}")

# =========================
# BOTÓN PARA ABRIR MODAL DE REGISTRO
# =========================
col_btn_modal, _ = st.columns([1, 3])
with col_btn_modal:
    if st.button("➕ Nuevo Registro", key="btn_nuevo", use_container_width=True):
        st.session_state.show_modal = True

# =========================
# MODAL DE REGISTRO
# =========================
@st.dialog("📝 Registrar Nuevo Carbón", width="large")
def modal_registro():
    st.markdown("### 📊 Ingrese los Datos del Registro")

    fecha = st.date_input("📅 Fecha del Registro", key="modal_fecha")

    with engine.connect() as conn:
        ultimo = conn.execute(text("""
            SELECT fecha, stock_final
            FROM registro_insumo
            WHERE id_sucursal = :id_sucursal
              AND id_insumo = 1
              AND estado = 1
            ORDER BY fecha DESC
            LIMIT 1
        """), {"id_sucursal": id_sucursal}).fetchone()

        venta_data = conn.execute(text("""
            SELECT COALESCE(venta_total, 0)
            FROM registro_insumo
            WHERE id_sucursal = :id_sucursal
              AND fecha = :fecha
            LIMIT 1
        """), {"id_sucursal": id_sucursal, "fecha": fecha}).fetchone()

        existe = conn.execute(text("""
            SELECT COUNT(*)
            FROM registro_insumo
            WHERE id_sucursal = :id_sucursal
              AND fecha = :fecha
              AND id_insumo = 1
              AND estado = 1
        """), {"id_sucursal": id_sucursal, "fecha": fecha}).scalar()

    if existe > 0:
        st.error("❌ Ya existe un registro activo para esta fecha.")
        return

    if ultimo:
        stock_inicial = float(ultimo.stock_final or 0)
        st.info(f"📦 **Stock Inicial automático:** {stock_inicial} kg (del día {ultimo.fecha})")
    else:
        stock_inicial = 0.0
        st.info("📦 Primer día registrado — Stock Inicial = 0")

    st.number_input("📦 Stock Inicial (kg)", value=stock_inicial, disabled=True)

    col1, col2 = st.columns(2)
    with col1:
        ingreso = st.number_input("📥 Ingreso (kg)", min_value=0.0, step=10.0)
    with col2:
        reposicion = st.number_input("🔄 Reposición (kg)", min_value=0.0, step=10.0)

    hora_actual = datetime.now().time()
    puede_stock_final = fecha < datetime.now().date() or hora_actual >= time(19, 0)

    if puede_stock_final:
        stock_final = st.number_input("📦 Stock Final (kg)", min_value=0.0, step=10.0)
    else:
        stock_final = 0.0
        st.info("⏳ El stock final solo puede ingresarse luego de las 7:00 PM.")

    venta_total = float(venta_data[0]) if venta_data else 0.0

    consumo = stock_inicial + ingreso + reposicion - stock_final
    ratio = (consumo / venta_total) if venta_total > 0 else 0.0

    st.divider()
    st.metric("🔥 Consumo (kg)", round(consumo, 2))
    st.metric("💰 Venta Total (S/.)", round(venta_total, 2))
    st.metric("📊 Ratio", round(ratio, 4))
    st.metric("📈 Ratio %", f"{round(ratio * 100, 2)}%")

    if st.button("💾 Guardar Registro", use_container_width=True):
        try:
            with engine.begin() as conn:
                conn.execute(text("""
                    INSERT INTO registro_insumo(
                        id_insumo, id_sucursal, id_usuario, fecha,
                        stock_inicial, ingreso, consumo, reposicion,
                        stock_final, venta_total, ratio, estado
                    )
                    VALUES(
                        1, :id_sucursal, :id_usuario, :fecha,
                        :stock_inicial, :ingreso, :consumo, :reposicion,
                        :stock_final, :venta_total, :ratio, 1
                    )
                """), {
                    "id_sucursal": id_sucursal,
                    "id_usuario": id_usuario,
                    "fecha": fecha,
                    "stock_inicial": stock_inicial,
                    "ingreso": ingreso,
                    "consumo": consumo,
                    "reposicion": reposicion,
                    "stock_final": stock_final,
                    "venta_total": venta_total,
                    "ratio": ratio
                })

            st.success("Registro guardado exitosamente.")
            st.session_state.show_modal = False
            st.rerun()

        except Exception as e:
            st.error("Error al guardar registro.")
            st.exception(e)

if st.session_state.get("show_modal", False):
    modal_registro()

# =========================
# FUNCIÓN ESTADO
# =========================
def ratio_estado_emoji(r):
    try:
        r = float(r)
    except:
        return ""

    # Si es decimal (menos de 1), conviértelo a porcentaje
    if r < 1:
        r = r * 100

    if r > 55:
        return "🔴"   # Excesivo
    elif r < 45:
        return "🟢"   # Controlado
    else:
        return "🟠"   # Normal

# Inicializar session_state
st.session_state.setdefault("edit_mode", False)
st.session_state.setdefault("fechas_a_editar", [])
st.session_state.setdefault("delete_mode", False)
st.session_state.setdefault("fecha_delete", None)
st.session_state.setdefault("ultimo_stock_final_editado", None)

# =========================
# HISTORIAL
# =========================
st.divider()

with st.expander("📊 Ver Historial de Carbón (Rango de Fechas)", expanded=True):
    c1, c2 = st.columns(2)
    with c1:
        fecha_inicio = st.date_input("📅 Fecha inicio", value=datetime.now().replace(day=1).date())
    with c2:
        fecha_fin = st.date_input("📅 Fecha fin", value=datetime.now().date())

    if fecha_inicio > fecha_fin:
        st.error("❌ La fecha de inicio no puede ser mayor que la fecha fin")
    else:
        with engine.connect() as conn:
            df = pd.read_sql(text("""
                SELECT
                    ri.fecha,
                    ri.stock_inicial,
                    ri.ingreso,
                    ri.consumo,
                    COALESCE(ri.reposicion,0) AS reposicion,
                    ri.stock_final,
                    ri.venta_total,
                    ROUND(ri.ratio * 100,2) AS ratio_pct,
                    i.nombre AS tipo_carbon
                FROM registro_insumo ri
                JOIN insumos i ON i.id_insumo = ri.id_insumo
                WHERE ri.id_sucursal = :id_sucursal
                  AND ri.id_insumo = 1
                  AND ri.estado = 1
                  AND i.estado = 1
                  AND ri.fecha BETWEEN :fi AND :ff
                ORDER BY ri.fecha ASC
            """), conn, params={"id_sucursal": id_sucursal, "fi": fecha_inicio, "ff": fecha_fin})

        if df.empty:
            st.info("📭 No hay registros en este rango")
        else:
            df_display = df.copy()
            df_display["fecha"] = pd.to_datetime(df_display["fecha"]).dt.date
            df_display["Fecha"] = df_display["fecha"].apply(lambda x: x.strftime("%d/%m/%Y"))
            df_display["Ratio %"] = df_display["ratio_pct"].apply(lambda x: f"{x:.2f}%")

            st.dataframe(
                df_display[[
                    "Fecha", "stock_inicial", "ingreso", "consumo", "reposicion",
                    "stock_final", "venta_total", "Ratio %", "tipo_carbon"
                ]],
                use_container_width=True,
                hide_index=True
            )

            st.markdown("### 🔧 Acciones por registro")
            for i, row in df_display.iterrows():
                fecha_date = row["fecha"]
                key = f"{fecha_date.isoformat()}_{i}"

                col_desc, col_edit, col_del = st.columns([6, 1, 1])
                with col_desc:
                    st.write(
                        f"📅 **{fecha_date.strftime('%d/%m/%Y')}** — "
                        f"Consumo: {row['consumo']} kg | "
                        f"Venta: S/. {row['venta_total']} | "
                        f"Ratio: {row['Ratio %']} {ratio_estado_emoji(row['ratio_pct'])}"
                    )
                with col_edit:
                    if st.button("✏️", key=f"edit_{key}"):
                        st.session_state["edit_mode"] = True
                        st.session_state["fechas_a_editar"] = [fecha_date]
                        safe_rerun()
                with col_del:
                    if st.button("🗑️", key=f"del_{key}"):
                        st.session_state["delete_mode"] = True
                        st.session_state["fecha_delete"] = fecha_date
                        safe_rerun()

            # Resumen
            st.divider()
            st.markdown("### 📊 Resumen del rango")

            consumo_total = df["consumo"].sum()
            venta_total_mes = df["venta_total"].sum()
            ratio_mes = (consumo_total / venta_total_mes) * 100 if venta_total_mes > 0 else 0

            def normalizar_ratio(r):
             """Convierte decimal a porcentaje si es necesario."""
             return r * 100 if r < 1 else r

            ratio_eval = normalizar_ratio(ratio_mes)

            meta_pct = 55
            if ratio_eval > meta_pct:
             color = "#ff6b6b"; estado = "⚠️ Ratio Excesivo"
            elif ratio_eval < 45:
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

# =========================
# EDICIÓN INDIVIDUAL
# =========================
if st.session_state.get("edit_mode", False):
    fecha_editar = st.session_state["fechas_a_editar"][0]

    with engine.connect() as conn:
        data = conn.execute(text("""
            SELECT stock_inicial, ingreso, reposicion, stock_final, consumo, venta_total
            FROM registro_insumo
            WHERE id_sucursal = :id_sucursal
              AND fecha = :fecha
              AND id_insumo = 1
              AND estado = 1
            LIMIT 1
        """), {"id_sucursal": id_sucursal, "fecha": fecha_editar}).fetchone()

    if not data:
        st.error("Registro no encontrado")
        st.session_state["edit_mode"] = False
        safe_rerun()

    st.markdown(f"### ✏️ Editar registro — {fecha_editar.strftime('%d/%m/%Y')}")

    with st.form("form_editar_individual"):
        stock_inicial_e = st.number_input("Stock Inicial", value=float(data[0]))
        ingreso_e = st.number_input("Ingreso", value=float(data[1]))
        reposicion_e = st.number_input("Reposición", value=float(data[2]))
        stock_final_e = st.number_input("Stock Final", value=float(data[3]))
        venta_total_e = st.number_input("Venta Total", value=float(data[5]))

        guardar = st.form_submit_button("💾 Guardar cambios")
        cancelar = st.form_submit_button("Cancelar")

    if cancelar:
        st.session_state["edit_mode"] = False
        safe_rerun()

    if guardar:
        consumo_new = stock_inicial_e + ingreso_e + reposicion_e - stock_final_e
        ratio_new = consumo_new / venta_total_e if venta_total_e > 0 else 0

        try:
            with engine.begin() as conn:
                conn.execute(text("""
                    UPDATE registro_insumo
                    SET stock_inicial = :si,
                        ingreso = :ing,
                        reposicion = :rep,
                        stock_final = :sf,
                        consumo = :cons,
                        venta_total = :vt,
                        ratio = :rat
                    WHERE id_sucursal = :id_sucursal
                      AND fecha = :fecha
                      AND id_insumo = 1
                      AND estado = 1
                """), {
                    "si": stock_inicial_e,
                    "ing": ingreso_e,
                    "rep": reposicion_e,
                    "sf": stock_final_e,
                    "cons": consumo_new,
                    "vt": venta_total_e,
                    "rat": ratio_new,
                    "id_sucursal": id_sucursal,
                    "fecha": fecha_editar
                })

            # Guardamos el stock_final para recálculo del día siguiente
            st.session_state["ultimo_stock_final_editado"] = stock_final_e

            st.success("Registro actualizado")
            st.session_state["edit_mode"] = False
            safe_rerun()

        except Exception as e:
            st.error("Error actualizando")
            st.exception(e)

# =========================
# RECÁLCULO SIGUIENTE DÍA (solo si se editó)
# =========================
if st.session_state.get("ultimo_stock_final_editado") is not None:
    stock_final_e = st.session_state["ultimo_stock_final_editado"]
    fecha_editar = st.session_state["fechas_a_editar"][0]

    with engine.connect() as conn:
        siguiente = conn.execute(text("""
            SELECT fecha, stock_inicial, ingreso, reposicion, stock_final, venta_total
            FROM registro_insumo
            WHERE id_sucursal = :id_sucursal
              AND id_insumo = 1
              AND estado = 1
              AND fecha > :fecha
            ORDER BY fecha ASC
            LIMIT 1
        """), {"id_sucursal": id_sucursal, "fecha": fecha_editar}).fetchone()

    if siguiente:
        nueva_fecha = siguiente.fecha

        nuevo_si = stock_final_e

        consumo_nuevo = (
            nuevo_si
            + float(siguiente.ingreso or 0)
            + float(siguiente.reposicion or 0)
            - float(siguiente.stock_final or 0)
        )

        ratio_nuevo = (
            consumo_nuevo / float(siguiente.venta_total)
            if (siguiente.venta_total and float(siguiente.venta_total) > 0)
            else 0
        )

        with engine.begin() as conn:
            conn.execute(text("""
                UPDATE registro_insumo
                SET stock_inicial = :si,
                    consumo = :cons,
                    ratio = :rat
                WHERE id_sucursal = :id_sucursal
                  AND fecha = :fecha
                  AND id_insumo = 1
            """), {
                "si": nuevo_si,
                "cons": consumo_nuevo,
                "rat": ratio_nuevo,
                "id_sucursal": id_sucursal,
                "fecha": nueva_fecha
            })

    # Limpiar estado
    st.session_state["ultimo_stock_final_editado"] = None
    st.session_state["fechas_a_editar"] = []

# =========================
# ELIMINAR REGISTRO
# =========================
if st.session_state.get("delete_mode", False):
    fecha_borrar = st.session_state.get("fecha_delete")

    st.markdown(f"### 🗑️ Eliminar registro — {fecha_borrar.strftime('%d/%m/%Y')}")
    st.write("¿Deseas eliminar este registro?")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Cancelar"):
            st.session_state["delete_mode"] = False
            st.session_state["fecha_delete"] = None
            safe_rerun()
    with c2:
        if st.button("Eliminar", type="primary"):
            try:
                with engine.begin() as conn:
                    conn.execute(text("""
                        UPDATE registro_insumo
                        SET estado = 0
                        WHERE id_sucursal = :id_sucursal
                          AND fecha = :fecha
                          AND id_insumo = 1
                    """), {"id_sucursal": id_sucursal, "fecha": fecha_borrar})

                st.success("Registro eliminado correctamente")
                st.session_state["delete_mode"] = False
                st.session_state["fecha_delete"] = None
                safe_rerun()

            except Exception as e:
                st.error("Error eliminando")
                st.exception(e)
