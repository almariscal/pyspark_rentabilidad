import pandas as pd

# Ruta al resultado
resultado_path = "output_data/resultado_cups.parquet"
excel_output_path = "output_data/resultado_final.xlsx"

# 1. Leer DataFrame
df = pd.read_parquet(resultado_path)

# 2. Estadísticas agregadas
resumen = df.describe(include="all")

# 3. Exportar a Excel con varias hojas
with pd.ExcelWriter(excel_output_path, engine='xlsxwriter') as writer:
    df.to_excel(writer, sheet_name='datos', index=False)
    resumen.to_excel(writer, sheet_name='resumen')

print(f"✅ Exportado correctamente a '{excel_output_path}' con hojas: 'datos' y 'resumen'")
