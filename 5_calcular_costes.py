from pyspark.sql import SparkSession
from pyspark.sql.functions import col, sum as sum_, to_timestamp, avg

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

# Lectura
curvas = spark.read.option("timestampAsString", "true").parquet(curva_path).withColumn("datetime", to_timestamp("datetime"))
omie = spark.read.option("timestampAsString", "true").parquet(omie_path).withColumn("datetime", to_timestamp("datetime"))
servicios = spark.read.option("timestampAsString", "true").parquet(servicios_path).withColumn("datetime", to_timestamp("datetime"))
calendario = spark.read.option("timestampAsString", "true").parquet(calendario_path).withColumn("datetime", to_timestamp("datetime"))

# Unión
consumos = curvas \
    .join(omie, on="datetime", how="left") \
    .join(servicios, on="datetime", how="left") \
    .join(calendario, on="datetime", how="left")

# Agregación por cliente y periodo
agrupado = consumos.groupBy("cups", "periodo").agg(
    sum_(col("kwh")).alias("kwh_total"),
    sum_((col("kwh") * col("precio_omie"))).alias("coste_omie_ponderado"),
    sum_((col("kwh") * col("precio_servicio"))).alias("coste_servicio_ponderado"),
    avg(col("precio_omie")).alias("precio_omie_medio"),
    avg(col("precio_servicio")).alias("precio_servicio_medio")
)

# Cálculo de precio medio ponderado
agrupado = agrupado.withColumn("coste_omie_ponderado", col("coste_omie_ponderado") / col("kwh_total"))
agrupado = agrupado.withColumn("coste_servicio_ponderado", col("coste_servicio_ponderado") / col("kwh_total"))

# Pivot para obtener una fila por cliente
pivot_df = agrupado.groupBy("cups").pivot("periodo", ["P1", "P2", "P3"]).agg(
    sum_("kwh_total").alias("kwh"),
    sum_("coste_omie_ponderado").alias("coste_omie"),
    sum_("coste_servicio_ponderado").alias("coste_servicio"),
    sum_("precio_omie_medio").alias("precio_omie_medio"),
    sum_("precio_servicio_medio").alias("precio_servicio_medio")
)

# Guardado
pivot_df.write.mode("overwrite").parquet(f"{base_path}/resultado_cups.parquet")
