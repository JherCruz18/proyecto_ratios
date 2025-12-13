import subprocess
import sys

# Conexión a tu BD local
db_host = "localhost"
db_port = "5432"
db_user = "postgres"
db_name = "controles_ratios"
db_password = "1234"

# Archivo de salida
output_file = "controles_ratios.sql"

# Configurar variable de entorno para la contraseña
import os
os.environ['PGPASSWORD'] = db_password

# Comando pg_dump usando la ruta completa si está disponible
try:
    # Intentar encontrar pg_dump en rutas comunes
    pg_dump_paths = [
        r"C:\Program Files\PostgreSQL\16\bin\pg_dump.exe",
        r"C:\Program Files\PostgreSQL\15\bin\pg_dump.exe",
        r"C:\Program Files\PostgreSQL\14\bin\pg_dump.exe",
        r"C:\Program Files (x86)\PostgreSQL\16\bin\pg_dump.exe",
        "pg_dump"
    ]
    
    pg_dump_cmd = None
    for path in pg_dump_paths:
        if os.path.exists(path) or path == "pg_dump":
            pg_dump_cmd = path
            break
    
    if not pg_dump_cmd:
        print("❌ pg_dump no encontrado. Revisa dónde está instalado PostgreSQL.")
        sys.exit(1)
    
    # Comando para exportar
    cmd = [
        pg_dump_cmd,
        "-h", db_host,
        "-p", db_port,
        "-U", db_user,
        "-d", db_name,
        "-f", output_file
    ]
    
    print(f"📦 Exportando BD '{db_name}' a '{output_file}'...")
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    
    print(f"✅ BD exportada correctamente a: {output_file}")
    print(f"📊 Tamaño: {os.path.getsize(output_file) / 1024:.2f} KB")
    
except subprocess.CalledProcessError as e:
    print(f"❌ Error al exportar: {e.stderr}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
