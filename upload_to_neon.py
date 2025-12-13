import subprocess
import sys
import os

# Tu conexión de Neon
neon_connection = "postgresql://neondb_owner:npg_2tdV7qBJreQY@ep-wandering-recipe-afrd7w6m-pooler.c-2.us-west-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
sql_file = "controles_ratios.sql"

# Rutas donde podría estar psql
psql_paths = [
    r"C:\Program Files\PostgreSQL\16\bin\psql.exe",
    r"C:\Program Files\PostgreSQL\15\bin\psql.exe",
    r"C:\Program Files\PostgreSQL\14\bin\psql.exe",
    r"C:\Program Files (x86)\PostgreSQL\16\bin\psql.exe",
    "psql"
]

psql_cmd = None
for path in psql_paths:
    if os.path.exists(path) or path == "psql":
        psql_cmd = path
        break

if not psql_cmd:
    print("❌ psql no encontrado.")
    print("Por favor, instala PostgreSQL Client o usa la interfaz web de Neon.")
    sys.exit(1)

try:
    print(f"📤 Subiendo BD a Neon desde '{sql_file}'...")
    
    cmd = [psql_cmd, neon_connection, "-f", sql_file]
    
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    
    print("✅ BD subida a Neon exitosamente!")
    print(result.stdout)
    
except subprocess.CalledProcessError as e:
    print(f"❌ Error: {e.stderr}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
