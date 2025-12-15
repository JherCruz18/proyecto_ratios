import pandas as pd
from sqlalchemy import text
from openpyxl import load_workbook
from db import engine


def exportar_carbon_excel(
    id_sucursal,
    nombre_sucursal,
    fecha_inicio,
    fecha_fin,
    plantilla="formato.xlsx",
    salida="Reporte_Carbon.xlsx"
):
    with engine.connect() as conn:
        df = pd.read_sql(
            text("""
                SELECT
                    ri.fecha,
                    ri.stock_inicial,
                    ri.ingreso,
                    COALESCE(ri.reposicion, 0) AS reposicion,
                    ri.stock_final,
                    ri.venta_total,
                    i.nombre AS tipo_carbon
                FROM registro_insumo ri
                JOIN insumos i ON i.id_insumo = ri.id_insumo
                WHERE ri.id_sucursal = :id_sucursal
                  AND ri.id_insumo = 1
                  AND ri.estado = 1
                  AND ri.fecha BETWEEN :fi AND :ff
                ORDER BY ri.fecha ASC
            """),
            conn,
            params={
                "id_sucursal": id_sucursal,
                "fi": fecha_inicio,
                "ff": fecha_fin
            }
        )

    if df.empty:
        raise ValueError("No hay datos para el rango seleccionado")

    wb = load_workbook(plantilla)
    ws = wb.active

    ws["D3"] = nombre_sucursal

    fila = 7
    for _, r in df.iterrows():
        ws[f"C{fila}"] = r["fecha"].strftime("%d/%m/%Y")
        ws[f"D{fila}"] = r["stock_inicial"]
        ws[f"E{fila}"] = r["ingreso"]
        ws[f"G{fila}"] = r["reposicion"]
        ws[f"H{fila}"] = r["stock_final"]
        ws[f"I{fila}"] = r["venta_total"]
        ws[f"K{fila}"] = r["tipo_carbon"]
        fila += 1

    wb.save(salida)
    return salida
