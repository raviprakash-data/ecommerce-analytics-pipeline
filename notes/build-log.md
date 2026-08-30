# Build Log

## 2026-08-12 — Databricks Lakehouse Setup

### Unity Catalog Setup

- **Catalog:** `retail_lakehouse`
- **Schemas created:**
  - `bronze`
  - `silver`
  - `gold`
- **Raw files volume:** `retail_lakehouse.bronze.raw_files`
- **Volume path:** `/Volumes/retail_lakehouse/bronze/raw_files/`
- **Workspace URL:** `https://dbc-c25a29d7-e216.cloud.databricks.com/explore/data/workspace?o=7474652242704980`

### Architecture

```text
retail_lakehouse (Catalog)
│
├── bronze (Schema)
│   └── raw_files (Volume)
│
├── silver (Schema)
│
└── gold (Schema)

## 2026-08-14 — Olist Raw Data Uploaded

### Raw Files

The 9 Olist dataset CSV files were uploaded to:

`/Volumes/retail_lakehouse/bronze/raw_files/`

Files:

1. `olist_customers_dataset.csv`
2. `olist_geolocation_dataset.csv`
3. `olist_order_items_dataset.csv`
4. `olist_order_payments_dataset.csv`
5. `olist_order_reviews_dataset.csv`
6. `olist_orders_dataset.csv`
7. `olist_products_dataset.csv`
8. `olist_sellers_dataset.csv`
9. `product_category_name_translation.csv`

### File Sizes

Approximate sizes were not recorded during upload.

### Purpose

These files represent the raw source data and will be used as the input for the Bronze ingestion process.

## 2026-08-14 — Bronze Orders Ingestion

### Orders

- Source file: `olist_orders_dataset.csv`
- Source path: `/Volumes/retail_lakehouse/bronze/raw_files/`
- Bronze table: `retail_lakehouse.bronze.orders`
- Row count: `99441`
- Format: Delta
- Write mode: overwrite

### Audit Columns

Added the following Bronze audit columns:

- `ingestion_timestamp` — records when the pipeline ingests the data.
- `source_file` — records the source file from which the record was ingested.

### Verification

Verified the Bronze table using:

```sql
SELECT *
FROM retail_lakehouse.bronze.orders
LIMIT 10;

## Category Name — Silver

- Source: `retail_lakehouse.bronze.category_name`
- Target: `retail_lakehouse.silver.category_name`
- Records: 71
- NULLs: 0
- Duplicates: 0
- Whitespace/case/empty-string issues: None
- Audit columns: Valid

### Business Completeness

A `LEFT ANTI JOIN` against `products` identified 3 unmatched category values:
`pc_gamer`, `portateis_cozinha_e_preparadores_de_alimentos`, and `NULL`.

### Decision

No unnecessary cleansing transformations were applied because the source passed
the technical quality checks.

The Gold layer will use a `LEFT JOIN` for category translation so unmatched
product categories are retained.