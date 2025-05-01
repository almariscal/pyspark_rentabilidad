import pandas as pd
import numpy as np
import random
import os
from datetime import datetime, timedelta
from tqdm import tqdm

# Configuración
NUM_CLIENTS = 11_000
BATCH_SIZE = 1_000
START_DATE = datetime(2024, 1, 1)
END_DATE = datetime(2025, 1, 1)
START_DATE_OMIE = datetime(2024, 1, 1)
END_DATE_OMIE = datetime(2026, 1, 1)
OUTPUT_DIR = "output_data"
CURVA_DIR = os.path.join(OUTPUT_DIR, "curvas_por_lotes")
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(CURVA_DIR, exist_ok=True)

# 1. Clientes
def generate_cups(index):
    return f"ES{str(index).zfill(18)}"

random.seed(42)
clientes = pd.DataFrame({
    "cups": [generate_cups(i) for i in range(NUM_CLIENTS)],
    "fecha_inicio": [START_DATE + timedelta(days=random.randint(0, 364)) for _ in range(NUM_CLIENTS)]
})
clientes.to_csv(f"{OUTPUT_DIR}/clientes.csv", index=False)
clientes.to_parquet(f"{OUTPUT_DIR}/clientes.parquet", index=False)

# 2. Perfil estándar diario (24 horas)
perfil_diario = np.array([
    0.5, 0.4, 0.4, 0.35, 0.35, 0.4, 0.6, 0.8, 1.2, 1.6, 1.5, 1.3,
    1.2, 1.1, 1.1, 1.3, 1.6, 1.8, 2.0, 1.8, 1.6, 1.2, 0.8, 0.6
])

# 3. Curvas por lotes
print("▶️ Generando curvas horarias para todos los clientes...")
for start in tqdm(range(0, NUM_CLIENTS, BATCH_SIZE), desc="Clientes por lote"):
    end = min(start + BATCH_SIZE, NUM_CLIENTS)
    batch = clientes.iloc[start:end]

    curvas = []
    for _, row in batch.iterrows():
        cups = row["cups"]
        fecha_ini = row["fecha_inicio"]
        fecha_fin = fecha_ini + timedelta(days=365)
        horas = pd.date_range(start=fecha_ini, end=fecha_fin, freq="H", inclusive="left")

        # Repetir perfil diario para 365 días
        perfil_repetido = np.tile(perfil_diario, len(horas) // 24 + 1)[:len(horas)]

        # Variación por cliente
        variacion = np.random.normal(1.0, 0.1, len(horas))
        consumo = perfil_repetido * variacion
        consumo = np.clip(consumo, 0.1, 2.5)

        df = pd.DataFrame({
            "cups": cups,
            "datetime": horas,
            "kwh": consumo
        })
        curvas.append(df)

    curvas_df = pd.concat(curvas, ignore_index=True)
    curvas_df.to_csv(f"{CURVA_DIR}/curvas_{start}_{end-1}.csv", index=False)
    curvas_df.to_parquet(f"{CURVA_DIR}/curvas_{start}_{end-1}.parquet", index=False)

# 4. OMIE realista
print("▶️ Generando precios OMIE...")
fechas_horas = pd.date_range(start=START_DATE_OMIE, end=END_DATE_OMIE, freq="H", inclusive="left")
base_diaria = [
    10, 9.8, 9.5, 9.0, 8.8, 9.2, 10.5, 11.0, 11.2, 11.4, 11.5, 11.3,
    11.0, 10.7, 10.8, 11.2, 12.0, 13.0, 15.0, 25.0, 40.0, 55.0, 45.0, 30.0
]  # €/MWh
base_extendida = np.tile(base_diaria, len(fechas_horas) // 24 + 1)[:len(fechas_horas)]
variacion = np.random.normal(1.0, 0.12, len(fechas_horas))
precio_mwh = np.clip(base_extendida * variacion, 0, 90)
precio_omie = precio_mwh / 1000  # €/kWh
omie = pd.DataFrame({"datetime": fechas_horas, "precio_omie": precio_omie})
omie.to_csv(f"{OUTPUT_DIR}/omie.csv", index=False)
omie.to_parquet(f"{OUTPUT_DIR}/omie.parquet", index=False)

# 5. Servicios de ajuste
print("▶️ Generando precios de servicios de ajuste...")
precio_servicio = np.random.normal(loc=0.015, scale=0.004, size=len(fechas_horas))
precio_servicio = np.clip(precio_servicio, 0.005, 0.05)
servicios = pd.DataFrame({"datetime": fechas_horas, "precio_servicio": precio_servicio})
servicios.to_csv(f"{OUTPUT_DIR}/servicios_ajuste.csv", index=False)
servicios.to_parquet(f"{OUTPUT_DIR}/servicios_ajuste.parquet", index=False)

# 6. Calendario 2.0TD
print("▶️ Generando calendario 2.0TD...")
def asignar_periodo(dt):
    if dt.weekday() >= 5:
        return "P3"
    h = dt.hour
    if 10 <= h < 14 or 18 <= h < 22:
        return "P1"
    elif 8 <= h < 10 or 14 <= h < 18 or 22 <= h < 24:
        return "P2"
    else:
        return "P3"

calendario = pd.DataFrame({"datetime": fechas_horas})
calendario["periodo"] = calendario["datetime"].map(asignar_periodo)
calendario.to_csv(f"{OUTPUT_DIR}/calendario_periodos.csv", index=False)
calendario.to_parquet(f"{OUTPUT_DIR}/calendario_periodos.parquet", index=False)

print("✅ Todo generado correctamente en la carpeta:", OUTPUT_DIR)
