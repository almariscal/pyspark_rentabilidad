from pyspark.sql import SparkSession
from pyspark.sql.functions import col, sum as sum_, to_timestamp
import pandas as pd

# Inicializa Spark
spark = SparkSession.builder \
    .appName("CalculoRentabilidad") \
    .getOrCreate()

# Paths
base_path = "output_data"
curva_path = f"{base_path}/fixed_parquet/curvas_parquet_fix/*.parquet"
omie_path = f"{base_path}/fixed_parquet/omie_fix.parquet"
servicios_path = f"{base_path}/fixed_parquet/servicios_ajuste_fix.parquet"
calendario_path = f"{base_path}/fixed_parquet/calendario_periodos_fix.parquet"

# Leer con timestamp
curvas = spark.read.option("timestampAsString", "true").parquet(curva_path).withColumn("datetime", to_timestamp("datetime"))
omie = spark.read.option("timestampAsString", "true").parquet(omie_path).withColumn("datetime", to_timestamp("datetime"))
servicios = spark.read.option("timestampAsString", "true").parquet(servicios_path).withColumn("datetime", to_timestamp("datetime"))
calendario = spark.read.option("timestampAsString", "true").parquet(calendario_path).withColumn("datetime", to_timestamp("datetime"))

# Filtrar los 3 primeros CUPS
primeros_cups = ["ES000000000000000000", "ES000000000000000001", "ES000000000000000002"]
curvas_filtradas = curvas.filter(col("cups").isin(primeros_cups))

# Unir datos
consumos = curvas_filtradas \
    .join(omie, on="datetime", how="left") \
    .join(servicios, on="datetime", how="left") \
    .join(calendario, on="datetime", how="left")

# Exportar datos horarios completos a Excel
df_horario = consumos.select("cups", "datetime", "kwh", "precio_omie", "precio_servicio", "periodo").toPandas()
df_horario.to_excel(f"{base_path}/detalle_horario_3cups.xlsx", index=False)

# Agregación
agrupado = consumos.groupBy("cups", "periodo").agg(
    sum_(col("kwh")).alias("kwh_total"),
    sum_((col("kwh") * col("precio_omie"))).alias("coste_omie_ponderado"),
    sum_((col("kwh") * col("precio_servicio"))).alias("coste_servicio_ponderado")
)
agrupado = agrupado.withColumn("precio_omie_medio", col("coste_omie_ponderado") / col("kwh_total"))
agrupado = agrupado.withColumn("precio_servicio_medio", col("coste_servicio_ponderado") / col("kwh_total"))

# Pivot
pivot_df = agrupado.groupBy("cups").pivot("periodo", ["P1", "P2", "P3"]).agg(
    sum_("kwh_total").alias("kwh"),
    sum_("coste_omie_ponderado").alias("coste_omie"),
    sum_("coste_servicio_ponderado").alias("coste_servicio"),
    sum_("precio_omie_medio").alias("precio_omie_medio"),
    sum_("precio_servicio_medio").alias("precio_servicio_medio")
)

# Guardar resultado agregado
pivot_df.write.mode("overwrite").parquet(f"{base_path}/resultado_cups.parquet")

print("✅ Datos horarios exportados a Excel:")
print(f"   → {base_path}/detalle_horario_3cups.xlsx")
