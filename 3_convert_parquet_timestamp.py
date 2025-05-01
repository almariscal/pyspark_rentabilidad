import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import os
from tqdm import tqdm

# Paths originales y destino
parquet_input_dirs = [
    "output_data/curvas_por_lotes",
]
parquet_single_files = [
    "output_data/omie.parquet",
    "output_data/servicios_ajuste.parquet",
    "output_data/calendario_periodos.parquet",
]

# Carpeta de salida
fixed_dir = "output_data/fixed_parquet"
os.makedirs(fixed_dir, exist_ok=True)

# 1. Reparar lotes de curvas
curvas_fixed = os.path.join(fixed_dir, "curvas_parquet_fix")
os.makedirs(curvas_fixed, exist_ok=True)

print("✅ Reparando ficheros de curvas por lotes...")
for fname in tqdm(os.listdir(parquet_input_dirs[0])):
    if fname.endswith(".parquet"):
        path = os.path.join(parquet_input_dirs[0], fname)
        df = pd.read_parquet(path)

        df["datetime"] = pd.to_datetime(df["datetime"]).astype("datetime64[ms]")
        df.to_parquet(os.path.join(curvas_fixed, fname), index=False)

# 2. Reparar ficheros individuales
for file_path in parquet_single_files:
    name = os.path.basename(file_path).replace(".parquet", "")
    output_path = os.path.join(fixed_dir, f"{name}_fix.parquet")

    print(f"✅ Reparando {name}.parquet...")
    df = pd.read_parquet(file_path)
    df["datetime"] = pd.to_datetime(df["datetime"]).astype("datetime64[ms]")
    df.to_parquet(output_path, index=False)

print("\n✅ Todos los ficheros Parquet han sido reparados y guardados en:")
print(f"   → {fixed_dir}")
