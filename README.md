# E-Commerce Analytics Lakehouse

> One-line description of what this does — fill in once the pipeline is complete.

## Architecture

*(Diagram goes here — fill in last, once the pipeline is finalized)*

## Tech Stack

| Tool | Role | Why |
|---|---|---|
| PySpark | Bronze/Silver/Gold transformation | Distributed processing on Databricks |
| Databricks Free Edition | Compute & storage | Serverless compute, Unity Catalog managed storage |
| Delta Lake | Storage format | ACID transactions, time travel, schema enforcement |
| Databricks Workflows | Orchestration | Automated Bronze → Silver → Gold scheduling with retries |
| Power BI | Serving / dashboard | Business-facing consumption layer |

## Project Structure

```
ecommerce-analytics-pipeline/
├── setup/
│   └── uc_volume_setup.sql
├── notebooks/
│   ├── 01_bronze/
│   ├── 02_silver/
│   ├── 03_gold/
│   └── 99_utils/
├── workflows/
│   └── databricks_job.yml
├── tests/
├── powerbi/
├── notes/
│   └── build-log.md
├── data/
│   └── sample/
└── README.md
```

## Data Source

[Olist Brazilian E-Commerce Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) — Brazilian e-commerce data containing 100K+ orders placed between 2016–2018, covering the customer journey from order placement through delivery and review.

The 9 raw CSV source files are stored in the Databricks Unity Catalog Volume:

`/Volumes/retail_lakehouse/bronze/raw_files/`

| Source File | Description |
|---|---|
| `olist_orders_dataset.csv` | Central order-level data including order status and timestamps |
| `olist_order_items_dataset.csv` | Line items per order including price, freight, product and seller |
| `olist_order_payments_dataset.csv` | Payment method, installments and payment value per order |
| `olist_order_reviews_dataset.csv` | Customer review scores and comments |
| `olist_customers_dataset.csv` | Customer identifiers and location information |
| `olist_sellers_dataset.csv` | Seller identifiers and location information |
| `olist_products_dataset.csv` | Product attributes and category information |
| `product_category_name_translation.csv` | Portuguese-to-English product category name mapping |
| `olist_geolocation_dataset.csv` | Brazilian ZIP-code prefix and geographic coordinates |
## Data Observations & Engineering Decisions

**Audit column naming inconsistency**
Initial Bronze dev iteration used `ingesttime` as the audit timestamp column name on a re-run of `orders`, while the original `ingest_orders` notebook had used `ingestion_timestamp`. Standardized on `ingestion_timestamp` across all 9 tables and re-ran ingestion with `overwriteSchema=true` to apply the fix cleanly. Lesson: define audit column names as constants once ingestion logic is parameterized, rather than relying on remembering a fixed string across notebooks.

**Null delivery timestamps in `orders`**
`order_delivered_carrier_date` and `order_delivered_customer_date` are null for orders that haven't reached those stages yet (e.g. `shipped`, `canceled`, `unavailable` statuses). This is expected, status-dependent behavior, not missing/broken data. To be validated explicitly in Silver: confirm the null pattern lines up with `order_status`, and flag any `delivered` order with a null delivery date as a genuine data quality issue rather than assuming all nulls are fine.

**`geolocation` scale vs. other tables**
`geolocation` ingested ~1,000,163 rows vs. ~99,000–112,000 for order-level tables. This is expected — it's ZIP-code-prefix-level geographic data, not order-level, so many rows map to the same order/customer. Confirms ingestion is capturing full source data rather than something being incorrectly filtered.

## Pipeline Layers

### Bronze — Raw Ingestion

All 9 raw Olist CSV files ingested from the Unity Catalog volume:

`/Volumes/retail_lakehouse/bronze/raw_files/`

Built as a single parameterized notebook (`ingest_bronze`) rather than one notebook per source — a config list of `(csv_filename, table_name)` pairs drives a shared ingestion function, so every table goes through identical, reviewable logic:

- `header=True`, `inferSchema=True` on CSV read
- `ingestion_timestamp` and `source_file` audit columns added to every row
- Written as Delta tables under `retail_lakehouse.bronze`, `mode="overwrite"` (appropriate for this static, one-time dataset — see note below on why `overwrite` was chosen over `append`/`merge`)

**Write mode decision:** `overwrite` was used since the Olist dataset is static (no daily-changing source). For data that changes over time — e.g. an `orders` table where existing rows get status updates — `append` alone would create duplicate rows for the same entity, since `append` has no concept of record identity. That case requires `MERGE` (upsert: update if the record exists, insert if it doesn't). `append` alone is only safe for genuinely immutable, event-style data (logs, clickstream, sensor readings) where a record, once written, never changes.

| Bronze Table | Row Count |
|---|---|
| `orders` | 99,441 |
| `order_items` | 112,650 |
| `order_payments` | 103,886 |
| `order_reviews` | 104,162 |
| `customers` | 99,441 |
| `sellers` | 3,095 |
| `products` | 32,951 |
| `category_name` | 71 |
| `geolocation` | 1,000,163 |

### Silver — Cleaning & Standardisation

Silver applies data-quality validation and business-rule-based transformations
before data is used by the Gold layer.

Current progress:

- `category_name` — completed
  - 71 records validated
  - No NULL values
  - No duplicate records
  - No whitespace or casing issues
  - Audit columns validated
  - Business completeness checked against `products`
  - 3 unmatched category values identified: `pc_gamer`,
    `portateis_cozinha_e_preparadores_de_alimentos`, and `NULL`
  - No unsupported manual corrections applied
  - Gold will use a `LEFT JOIN` when applying category translations so
    unmatched product records are retained

- `orders` — completed
  - 99,441 records validated
  - No duplicate records
  - NULL values profiled against `order_status`
  - NULL counts identified:
    - `order_approved_at`: 160
    - `order_delivered_carrier_date`: 1,783
    - `order_delivered_customer_date`: 2,965
  - NULL delivery timestamps were analysed against `order_status`
  - 8 delivered orders missing customer delivery date identified
  - 0 approved-before-purchase violations found
  - 23 carrier-date-after-customer-date violations identified
  - Timestamp columns validated as `timestamp`
  - `order_status` validated for whitespace and casing
  - Data-quality flags added instead of deleting or modifying affected records
  - Final row count validated: 99,441
  - Silver table written to `retail_lakehouse.silver.orders`

- `customers` — completed
  - 99,441 records validated
  - No NULL values
  - No duplicate records
  - No duplicate `customer_id` values
  - `customer_id` confirmed unique across all 99,441 records
  - `customer_unique_id` has 96,096 distinct values and can repeat
  - 27 distinct `customer_state` values identified
  - No leading/trailing whitespace found in `customer_city`
  - No casing issues found in `customer_city`
  - No cleansing transformation required because the source data already passed the checks
  - Final row count validated: 99,441
  - Silver table written to `retail_lakehouse.silver.customers`

- `sellers` — completed
  - 3,095 records validated
  - No NULL values
  - No duplicate complete records
  - No duplicate `seller_id` values
  - No leading/trailing whitespace found in `seller_city`
  - `seller_city` validated as lowercase
  - `seller_state` validated as uppercase
  - Data types validated
  - 23 distinct seller states identified
  - Seller ZIP code prefix range validated: `1,001` to `99,730`
  - No NULL seller ZIP code prefixes
  - Repeated ZIP code prefixes found across sellers and treated as valid because multiple sellers can share the same ZIP area
  - No seller associated with multiple states
  - No cleansing transformation required because the source data passed the validation checks
  - Final row count validated: 3,095
  - Silver table written to `retail_lakehouse.silver.sellers`

- `order_items` — pending
- `order_payments` — pending
- `order_reviews` — pending
- `products` — pending
- `geolocation` — pending

### Gold — Business Intelligence

| Model | Business Question |
|---|---|
| *(fill in)* | *(fill in)* |
| *(fill in)* | *(fill in)* |
| *(fill in)* | *(fill in)* |

## Data Quality Tests

*(Fill in as you write checks in Silver/Gold — list each test and what it catches, same format as the reference project.)*

| Test | What it checks |
|---|---|
| *(fill in)* | *(fill in)* |

## Orchestration

*(Fill in after setting up Databricks Workflows — task-by-task runtime, total pipeline time, retry/failure behavior.)*

## How to Run

### Prerequisites
- Databricks Free Edition workspace (with Unity Catalog, SQL warehouse)
- Kaggle account to download the dataset
- GitHub account

### Setup

**1. Clone the repository**
```bash
git clone <your-repo-url>
```

**2. Create the catalog, schemas, and volume**
Run the statements in `setup/uc_volume_setup.sql` in a Databricks SQL editor or notebook.

**3. Download the dataset**
Download the dataset from Kaggle and upload all 9 CSV files to your raw files volume (e.g. `/Volumes/<catalog>/bronze/raw_files/`).

**4. Run the pipeline**
Trigger the Databricks Workflow manually or on a schedule. It runs Bronze → Silver → Gold in sequence.

**5. Connect Power BI**
Connect Power BI Desktop to your Databricks SQL warehouse and open `powerbi/ecommerce_analytics.pbix`, or rebuild the dashboard against your Gold tables.

## Results

*(Fill in last — real numbers: total rows processed, % delivery SLA met, top category by revenue, pipeline runtime, DQ issues caught, etc.)*
