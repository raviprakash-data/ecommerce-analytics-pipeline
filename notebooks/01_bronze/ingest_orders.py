from pyspark.sql.functions import current_timestamp, lit

# Read raw orders CSV
df = spark.read.csv(
    "/Volumes/retail_lakehouse/bronze/raw_files/olist_orders_dataset.csv",
    header=True,
    inferSchema=True
)

# Check row count and schema
print("Row count:", df.count())
df.printSchema()

# Add audit columns
df = (
    df
    .withColumn("ingestion_timestamp", current_timestamp())
    .withColumn("source_file", lit("olist_orders_dataset.csv"))
)

# Write Bronze Delta table
df.write \
    .format("delta") \
    .mode("overwrite") \
    .saveAsTable("retail_lakehouse.bronze.orders")