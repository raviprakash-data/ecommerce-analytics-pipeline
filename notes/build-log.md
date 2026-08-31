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

---

## 2026-08-31 — Orders Silver Transformation

### Profiling

Completed profiling of the Bronze `orders` table.

- Row count: `99,441`
- Duplicate records: `0`
- Schema validated
- Timestamp columns confirmed as `timestamp`
- NULL values checked by column
- NULL patterns analysed against `order_status`
- `order_status` checked for whitespace and casing issues

### Business Rule Validation

#### Delivered Orders Missing Customer Delivery Date

Found `8` records where:

`order_status = 'delivered'`

and:

`order_delivered_customer_date IS NULL`

Added:

`is_delivered_missing_date`

The records were retained because the correct delivery date could not
be reliably determined.

#### Approval Before Purchase

Checked:

`order_approved_at < order_purchase_timestamp`

Result:

`0` violations

Added:

`is_approved_before_purchase`

#### Carrier Date After Customer Delivery Date

Checked:

`order_delivered_carrier_date > order_delivered_customer_date`

Result:

`23` violations

Added:

`is_carrier_after_customer_delivery`

The original timestamp values were retained and the records were flagged.

### Transformations

- Standardised `order_status` using `trim()` and `lower()`.
- Added three data-quality flags.
- No records were dropped.
- Existing timestamp columns were retained as `timestamp`.

### Final Validation

| Check | Result |
|---|---:|
| Bronze row count | `99,441` |
| Final Silver row count | `99,441` |
| Delivered missing customer date | `8` |
| Approved before purchase | `0` |
| Carrier after customer delivery | `23` |

The final row count matched Bronze exactly.

### Engineering Decision

Data-quality issues were flagged rather than deleted or manually corrected.
This preserves the original records while making potential issues visible
to downstream Gold-layer processing.

The validated dataset was written to:

`retail_lakehouse.silver.orders`