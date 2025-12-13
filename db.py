from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql+psycopg2://postgres:1234@localhost:5432/controles_ratios"

engine = create_engine(DATABASE_URL)

if __name__ == "__main__":
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM insumos LIMIT 1"))
        print("✅ Conexión OK:", result.fetchone())