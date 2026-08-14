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

*(Fill in as you find them — this is the most important section for interviews. Don't write it retroactively; log each issue in `notes/build-log.md` the moment you hit it, then summarize here.)*

**Example format:**

**[Issue name]**
What the raw data does wrong, why it matters, how you fixed it, what test/check catches it going forward.

## Pipeline Layers

### Bronze — Raw Ingestion

Raw Olist CSV files are stored in the Databricks Unity Catalog Volume:

`/Volumes/retail_lakehouse/bronze/raw_files/`

The Bronze layer reads the raw CSV files using PySpark with:

- `header=True` to treat the first row as column names.
- `inferSchema=True` to infer the data types.

Each Bronze table includes two audit columns:

- `ingestion_timestamp` — timestamp when the pipeline ingests the record.
- `source_file` — identifies the source CSV file.

The data is written as Delta tables under the `retail_lakehouse.bronze` schema.

For the initial development load, the tables use `overwrite` mode.

Example:

`olist_orders_dataset.csv` → `retail_lakehouse.bronze.orders`

### Silver — Cleaning & Standardisation
*(Fill in after Silver: what cleaning/dedup/join logic each model handles.)*

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
