from pyspark.sql.functions import current_timestamp, lit

files = [
    ("olist_orders_dataset", "orders"),
    ("olist_order_items_dataset", "order_items"),
    ("olist_order_payments_dataset", "order_payments"),
    ("olist_order_reviews_dataset", "order_reviews"),
    ("olist_customers_dataset", "customers"),
    ("olist_sellers_dataset", "sellers"),
    ("olist_products_dataset", "products"),
    ("product_category_name_translation", "category_name"),
    ("olist_geolocation_dataset", "geolocation"),
]

def ingest_csv_files(files):
    for csv_name, table_name in files:
        df = spark.read.csv(
            f"/Volumes/retail_lakehouse/bronze/raw_files/{csv_name}.csv",
            header=True,
            inferSchema=True,
        )

        df = df.withColumns({
            "ingestion_timestamp": current_timestamp(),
            "source_file": lit(csv_name),
        })

        row_count = df.count()

        df.write.format("delta") \
            .mode("overwrite") \
            .option("overwriteSchema", "true") \
            .saveAsTable(f"retail_lakehouse.bronze.{table_name}")

        print(f"{table_name}: {row_count} rows ingested from {csv_name}.csv")

ingest_csv_files(files)

# Sanity check
spark.sql("SHOW TABLES IN retail_lakehouse.bronze").show()