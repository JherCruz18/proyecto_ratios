import streamlit as st
from sqlalchemy import text
from db import engine
import pandas as pd
import hashlib
from datetime import datetime

# =================================================
# CONFIGURACIÓN
# =================================================
st.set_page_config(
    page_title="Administración de Usuarios",
    page_icon="👥",
    layout="wide"
)
st.title("👥 Administración de Usuarios - Logistica")

# =================================================
# VALIDACIÓN
# =================================================
if "id_usuario" not in st.session_state:
    st.warning("Debes iniciar sesión.")
    st.stop()

if st.session_state.get("rol") != "admin":
    st.error("⛔ Solo administradores pueden acceder.")
    st.stop()

# =================================================
# FUNCIONES
# =================================================
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def obtener_roles():
    with engine.connect() as conn:
        return pd.read_sql(text("""
            SELECT id_rol, nombre
            FROM rol
            WHERE estado = 1
            ORDER BY nombre
        """), conn)


def obtener_sucursales():
    with engine.connect() as conn:
        return pd.read_sql(text("""
            SELECT id_sucursal, nombre
            FROM sucursal
            WHERE estado = 1
            ORDER BY nombre
        """), conn)


def obtener_usuarios():
    with engine.connect() as conn:
        return pd.read_sql(text("""
            SELECT id_usuario, nombre, apellido, correo, telefono,
                   id_rol, id_sucursal, username, estado
            FROM usuario
            ORDER BY estado DESC, nombre
        """), conn)


def crear_usuario(data: dict):
    data["password"] = hash_password(data["password"])
    data["created_at"] = datetime.now()
    data["updated_at"] = datetime.now()

    # 🔒 asegurar tipos nativos
    data["id_rol"] = int(data["id_rol"])
    data["id_sucursal"] = int(data["id_sucursal"])

    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO usuario
            (nombre, apellido, correo, telefono,
             id_rol, id_sucursal, username,
             password, created_at, updated_at, estado)
            VALUES
            (:nombre, :apellido, :correo, :telefono,
             :id_rol, :id_sucursal, :username,
             :password, :created_at, :updated_at, 1)
        """), data)


def editar_usuario(id_usuario: int, data: dict):
    data["id_usuario"] = int(id_usuario)          # 🔒 FIX CRÍTICO
    data["id_rol"] = int(data["id_rol"])
    data["id_sucursal"] = int(data["id_sucursal"])
    data["updated_at"] = datetime.now()

    with engine.begin() as conn:
        conn.execute(text("""
            UPDATE usuario SET
                nombre = :nombre,
                apellido = :apellido,
                correo = :correo,
                telefono = :telefono,
                id_rol = :id_rol,
                id_sucursal = :id_sucursal,
                username = :username,
                updated_at = :updated_at
            WHERE id_usuario = :id_usuario
        """), data)


def actualizar_password(id_usuario: int, password: str):
    with engine.begin() as conn:
        conn.execute(text("""
            UPDATE usuario
            SET password = :password,
                updated_at = NOW()
            WHERE id_usuario = :id_usuario
        """), {
            "password": hash_password(password),
            "id_usuario": int(id_usuario)          # 🔒 FIX
        })


def desactivar_usuario(id_usuario: int):
    with engine.begin() as conn:
        conn.execute(text("""
            UPDATE usuario
            SET estado = 0
            WHERE id_usuario = :id
        """), {"id": int(id_usuario)})              # 🔒 FIX


def activar_usuario(id_usuario: int):
    with engine.begin() as conn:
        conn.execute(text("""
            UPDATE usuario
            SET estado = 1
            WHERE id_usuario = :id
        """), {"id": int(id_usuario)})              # 🔒 FIX

# =================================================
# CARGA DE DATA
# =================================================
roles = obtener_roles()
sucursales = obtener_sucursales()
usuarios = obtener_usuarios()

rol_dict = dict(zip(roles.id_rol, roles.nombre))
suc_dict = dict(zip(sucursales.id_sucursal, sucursales.nombre))

df = usuarios.copy()
df["rol"] = df["id_rol"].map(rol_dict)
df["sucursal"] = df["id_sucursal"].map(suc_dict)
df["estado_desc"] = df["estado"].map({1: "Activo", 0: "Inactivo"})

# =================================================
# FILTROS
# =================================================
st.subheader("🔍 Filtros")

f1, f2, f3 = st.columns([2, 1, 1])

with f1:
    filtro_texto = st.text_input("Buscar (nombre, apellido o username)")

with f2:
    filtro_rol = st.selectbox("Rol", ["Todos"] + list(roles.nombre))

with f3:
    filtro_sucursal = st.selectbox("Sucursal", ["Todas"] + list(sucursales.nombre))

df_f = df.copy()

if filtro_texto:
    t = filtro_texto.lower()
    df_f = df_f[df_f.apply(
        lambda r: t in str(r["nombre"]).lower()
        or t in str(r["apellido"]).lower()
        or t in str(r["username"]).lower(),
        axis=1
    )]

if filtro_rol != "Todos":
    df_f = df_f[df_f["rol"] == filtro_rol]

if filtro_sucursal != "Todas":
    df_f = df_f[df_f["sucursal"] == filtro_sucursal]

st.dataframe(
    df_f[
        ["nombre", "apellido", "username",
         "correo", "telefono", "rol",
         "sucursal", "estado_desc"]
    ],
    use_container_width=True,
    hide_index=True
)

# =================================================
# MODAL CREAR USUARIO
# =================================================
@st.dialog("➕ Crear Usuario")
def modal_crear_usuario():
    nombre = st.text_input("Nombre")
    apellido = st.text_input("Apellido")
    correo = st.text_input("Correo")
    telefono = st.text_input("Teléfono")
    username = st.text_input("Username")
    password = st.text_input("Contraseña", type="password")

    rol = st.selectbox("Rol", roles.nombre)
    suc = st.selectbox("Sucursal", sucursales.nombre)

    c1, c2 = st.columns(2)

    with c1:
        if st.button("💾 Guardar"):
            if not all([nombre, apellido, correo, username, password]):
                st.warning("Completa los campos obligatorios.")
            else:
                crear_usuario({
                    "nombre": nombre,
                    "apellido": apellido,
                    "correo": correo,
                    "telefono": telefono,
                    "id_rol": int(roles[roles.nombre == rol].id_rol.values[0]),
                    "id_sucursal": int(sucursales[sucursales.nombre == suc].id_sucursal.values[0]),
                    "username": username,
                    "password": password
                })
                st.success("Usuario creado correctamente.")
                st.rerun()

    with c2:
        if st.button("Cancelar"):
            st.rerun()

if st.button("➕ Crear Usuario"):
    modal_crear_usuario()

# =================================================
# MODAL EDITAR USUARIO
# =================================================
st.divider()
st.subheader("✏️ Editar Usuario")

usuarios_dict = {
    f"{r['nombre']} {r['apellido']} ({r['username']})": int(r["id_usuario"])
    for _, r in usuarios.iterrows()
}

usuario_sel = st.selectbox(
    "Selecciona un usuario",
    list(usuarios_dict.keys())
)

@st.dialog("✏️ Editar Usuario")
def modal_editar_usuario(row):
    nombre = st.text_input("Nombre", row["nombre"])
    apellido = st.text_input("Apellido", row["apellido"])
    correo = st.text_input("Correo", row["correo"])
    telefono = st.text_input("Teléfono", row["telefono"])
    username = st.text_input("Username", row["username"])

    rol = st.selectbox(
        "Rol",
        roles.nombre,
        index=list(roles.nombre).index(rol_dict[row["id_rol"]])
    )

    suc = st.selectbox(
        "Sucursal",
        sucursales.nombre,
        index=list(sucursales.nombre).index(suc_dict[row["id_sucursal"]])
    )

    new_pass = st.text_input("Nueva contraseña (opcional)", type="password")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        if st.button("💾 Guardar"):
            editar_usuario(int(row["id_usuario"]), {   # 🔒 FIX
                "nombre": nombre,
                "apellido": apellido,
                "correo": correo,
                "telefono": telefono,
                "id_rol": int(roles[roles.nombre == rol].id_rol.values[0]),
                "id_sucursal": int(sucursales[sucursales.nombre == suc].id_sucursal.values[0]),
                "username": username
            })

            if new_pass:
                actualizar_password(int(row["id_usuario"]), new_pass)

            st.success("Usuario actualizado.")
            st.rerun()

    with c2:
        if st.button("🛑 Desactivar"):
            desactivar_usuario(int(row["id_usuario"]))
            st.warning("Usuario desactivado.")
            st.rerun()

    with c3:
        if st.button("🟢 Activar"):
            activar_usuario(int(row["id_usuario"]))
            st.warning("Usuario activado.")
            st.rerun()

    with c4:
        if st.button("Cancelar"):
            st.rerun()

if st.button("✏️ Editar"):
    row_sel = usuarios[usuarios["id_usuario"] == usuarios_dict[usuario_sel]].iloc[0]
    modal_editar_usuario(row_sel)
