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

[Olist Brazilian E-Commerce Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) — 100K+ real orders placed between 2016–2018, covering the full customer journey from order placement to delivery and review.

| Table | Description |
|---|---|
| orders | Central transaction table — order status and timestamps |
| order_items | Line items per order — price, freight, product and seller |
| order_payments | Payment method and value per order |
| order_reviews | Customer review scores and comments |
| customers | Customer location and identifier |
| sellers | Seller location and identifier |
| products | Product attributes and category |
| product_category_translation | Portuguese to English category name mapping |
| geolocation | Brazilian zip code to lat/lng mapping |

## Data Observations & Engineering Decisions

*(Fill in as you find them — this is the most important section for interviews. Don't write it retroactively; log each issue in `notes/build-log.md` the moment you hit it, then summarize here.)*

**Example format:**

**[Issue name]**
What the raw data does wrong, why it matters, how you fixed it, what test/check catches it going forward.

## Pipeline Layers

### Bronze — Raw Ingestion
*(Fill in after building Bronze notebooks: what path CSVs are read from, what options were needed — e.g. multiline handling — what audit columns you added.)*

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
