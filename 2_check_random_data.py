import pandas as pd
import matplotlib.pyplot as plt
import glob
import random

# Ruta base
curva_dir = "output_data/curvas_por_lotes"
omie_path = "output_data/omie.parquet"

# 1. Leer curva de OMIE
df_omie = pd.read_parquet(omie_path)

# Mostrar curva de OMIE
plt.figure(figsize=(12, 4))
plt.plot(df_omie["datetime"], df_omie["precio_omie"], label="Precio OMIE (€/kWh)", color="green")
plt.title("Curva de precios OMIE 2024")
plt.xlabel("Fecha")
plt.ylabel("€/kWh")
plt.grid(True)
plt.tight_layout()
plt.legend()
plt.show()

# 2. Seleccionar aleatoriamente un archivo y un cliente
parquet_files = glob.glob(f"{curva_dir}/curvas_*.parquet")
df_sample = pd.read_parquet(random.choice(parquet_files))

# Escoger un cliente aleatorio del lote
cliente_id = random.choice(df_sample["cups"].unique())
df_cliente = df_sample[df_sample["cups"] == cliente_id]

# Mostrar curva de consumo del cliente
plt.figure(figsize=(12, 4))
plt.plot(df_cliente["datetime"], df_cliente["kwh"], label=f"Consumo {cliente_id}", color="blue")
plt.title(f"Curva de consumo - Cliente {cliente_id}")
plt.xlabel("Fecha")
plt.ylabel("kWh")
plt.grid(True)
plt.tight_layout()
plt.legend()
plt.show()
