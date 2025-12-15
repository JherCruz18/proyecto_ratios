import streamlit as st
from sqlalchemy import text
from db import engine

st.set_page_config(page_title="Login", layout="centered")
st.title("🔐 Iniciar Sesión")

usuario = st.text_input("Usuario")
password = st.text_input("Contraseña", type="password")

if st.button("Ingresar"):

    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT 
                    u.id_usuario,
                    u.username,
                    r.nombre AS rol,
                    u.id_sucursal,
                    s.nombre AS nombre_sucursal
                FROM usuario u
                JOIN rol r ON u.id_rol = r.id_rol
                LEFT JOIN sucursal s ON s.id_sucursal = u.id_sucursal
                WHERE u.username = :user 
                  AND u.password = :pass
                  AND r.estado = 1
            """),
            {"user": usuario, "pass": password}
        ).fetchone()

    if result:
        st.session_state["id_usuario"] = result.id_usuario
        st.session_state["username"] = result.username
        st.session_state["rol"] = result.rol
        st.session_state["id_sucursal"] = result.id_sucursal
        st.session_state["nombre_sucursal"] = result.nombre_sucursal  # ✅ CLAVE

        st.success("✅ Login correcto")

        # Redirección por rol
        if result.rol == "admin":
            st.switch_page("pages/admin_ventas.py")
        else:
            st.switch_page("pages/carbon.py")

    else:
        st.error("❌ Usuario o contraseña incorrectos")
