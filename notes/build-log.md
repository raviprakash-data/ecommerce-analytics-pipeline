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
```

---

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

---

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
```

---

## 2026-08-28 — Bronze: Remaining 8 Tables Ingested (Parameterized)

Rather than repeat the single-table pattern from `ingest_orders` 8 more times,
built a parameterized notebook (`ingest_bronze`). A config list of
`(csv_filename, table_name)` pairs drives one shared ingestion function, so every
table goes through identical, reviewable logic: read CSV, add audit columns,
write Delta.

### Row Counts (all 9 tables, verified with a SQL COUNT query)

| Table | Rows |
|---|---|
| orders | 99,441 |
| order_items | 112,650 |
| order_payments | 103,886 |
| order_reviews | 104,162 |
| customers | 99,441 |
| sellers | 3,095 |
| products | 32,951 |
| category_name | 71 |
| geolocation | 1,000,163 |

Total: 1,555,860 rows across 9 tables (about 15.5 lakh).

Verified against known Olist dataset scale before trusting the ingestion.
`geolocation` at about 1M rows versus about 100K for order-level tables is
expected: it is ZIP-prefix-level geographic data, not order-level.

### Issue: audit column naming inconsistency

An early iteration of the parameterized loop used `ingesttime` as the audit
timestamp column, while the original `ingest_orders` notebook used
`ingestion_timestamp`. Re-running the loop against the existing `orders` table did
not throw a schema-mismatch error as expected. This Delta/Databricks behavior is
worth testing deliberately later rather than assuming documented OSS behavior
applies as is.

Fix: standardized on `ingestion_timestamp` across all 9 tables and added
`overwriteSchema=true` so schema changes are deliberate, not accidental.

### Decision: write mode (overwrite vs append vs merge)

Chose `overwrite` because Olist is a static, one-time dataset with no
daily-changing source to reconcile against.

For future incremental projects: `append` only adds rows and has no concept of
record identity, so it is safe only for immutable data (event logs, clickstream,
sensor readings). Any table where an existing record can change over time for the
same identity (for example `orders`, where `order_status` moves from `shipped` to
`delivered`) needs `MERGE` (upsert). Plain `append` would create duplicate or
stale rows.

### Observation: null delivery timestamps in `orders`

`order_delivered_carrier_date` and `order_delivered_customer_date` are null for
orders that have not reached those stages (status-dependent, for example
`shipped`, `canceled`, `unavailable`). This is expected, not broken data. To be
validated in Silver: confirm the null pattern lines up with `order_status`, and
flag any `delivered` order with a null delivery date.

---

## [add date] — Category Name — Silver

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

On inspection these 8 are two different patterns. 7 have a valid
`order_delivered_carrier_date`, so the order shipped and the final delivery
timestamp is probably just missing. 1 has no carrier date either, which means it is
marked delivered with no shipping trail at all, a more serious inconsistency.

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

---

## 2026-09-01 — Customers Silver Validation

### Customers

- Source: `retail_lakehouse.bronze.customers`
- Target: `retail_lakehouse.silver.customers`
- Bronze row count: `99,441`
- Silver row count: `99,441`

### Data Quality Checks

- NULL values: `0`
- Duplicate complete records: `0`
- Duplicate `customer_id` values: `0`
- Distinct `customer_id` values: `99,441`
- Distinct `customer_unique_id` values: `96,096`
- Distinct `customer_state` values: `27`
- Leading/trailing whitespace in `customer_city`: None found
- Casing issues in `customer_city`: None found

### Customer ID Relationship

`customer_id` is unique across the table, while `customer_unique_id`
can appear multiple times.

This is expected because multiple `customer_id` records can belong to
the same underlying customer represented by `customer_unique_id`.

Gold implication: `customer_id` is effectively unique per order, not per person.
Any customer-level metric (repeat purchase rate, lifetime value) must group by
`customer_unique_id`, or every returning customer would be counted as new.

### Cleaning Decision

No cleansing transformation was required for `customer_city` because
the source data already passed the whitespace and casing checks.

No records were dropped or modified.

### Final Validation

Final row count matched the Bronze row count:

`99,441 = 99,441`

The validated DataFrame was written to:

`retail_lakehouse.silver.customers`

---

## 2026-09-02 — Sellers Silver Validation

### Sellers

- Source: `retail_lakehouse.bronze.sellers`
- Target: `retail_lakehouse.silver.sellers`
- Bronze row count: `3,095`
- Silver row count: `3,095`

### Data Quality Checks

- NULL values: `0`
- Duplicate complete records: `0`
- Duplicate `seller_id` values: `0`
- Leading/trailing whitespace in `seller_city`: None found
- Casing issues in `seller_city`: None found
- Casing issues in `seller_state`: None found
- NULL seller ZIP code prefixes: `0`
- Distinct seller states: `23`
- Seller ZIP code prefix range: `1,001` to `99,730`

### Seller ID Validation

`seller_id` was confirmed to be unique across the dataset.

No seller was found to be associated with multiple `seller_state` values.

### ZIP Code Validation

Multiple sellers can have the same `seller_zip_code_prefix`.

This was treated as valid because a ZIP code prefix represents a geographic area
and is not expected to be unique to a seller.

### Cleaning Decision

No cleansing transformation was required.

The source data already passed the whitespace, casing, NULL, duplicate,
datatype, and business relationship checks.

No records were dropped or manually modified.

### Final Validation

Final row count matched the Bronze row count:

`3,095 = 3,095`

The validated DataFrame was written to:

`retail_lakehouse.silver.sellers`

---

## 2026-09-03 — Silver Products

### Objective

Profile, validate, standardize, and write the Products dataset into the Silver layer.

### Source and Target

- Source: `retail_lakehouse.bronze.products`
- Target: `retail_lakehouse.silver.products`

### Profiling

- Bronze row count: `32,951`
- Duplicate `product_id` values: `0`

### NULL Findings

- `product_category_name`, `product_name_lenght`, `product_description_lenght` and
  `product_photos_qty` each have `610` NULLs. The identical count across four columns
  suggests the same incomplete listings, although the row overlap was not explicitly
  checked.
- `product_weight_g`, `product_length_cm`, `product_height_cm` and
  `product_width_cm` each have `2` NULLs.

### Category Validation

Checked product categories against `silver.category_name` with a `LEFT ANTI JOIN`.
`13` products have a non-null category with no translation (`pc_gamer` and
`portateis_cozinha_e_preparadores_de_alimentos`). Category translation is deferred
to Gold, which will use a `LEFT JOIN` so these products are retained.

### Physical Attribute Validation

- Negative values: `0`
- `4` products have `product_weight_g = 0`, and all four share identical dimensions
  (30 x 25 x 30 cm), which suggests placeholder values rather than real measurements.
  The true weight is unknown, so they were left unchanged.
- The first version of this check used `< 0` and reported zero problems. Re-running with
  `<= 0` found the 4 zero-weight products. Lesson: check boundary conditions
  deliberately.

### Transformations

Corrected misspelled source column names:

- `product_name_lenght` → `product_name_length`
- `product_description_lenght` → `product_description_length`

No rows were dropped and no values were imputed. Audit columns were preserved.

### Final Validation

Final row count matched the Bronze row count:

`32,951 = 32,951`

The validated DataFrame was written to:

`retail_lakehouse.silver.products`

---

## 2026-09-04 — Silver: order_items (completed)

- Source: `retail_lakehouse.bronze.order_items`, 112,650 rows, matching the Bronze count.
- Schema checked: `price` and `freight_value` are double, `order_item_id` is integer, `shipping_limit_date` is already timestamp, so no casting was needed.
- Nulls: zero in every column, including all four join keys.
- Key: `order_id` + `order_item_id` is a unique composite key. `order_id` alone repeats by design, since one order can have several items. This also means no full-row duplicates exist.
- Orphan checks (left_anti against Silver tables): 0 orphan `order_id` vs `silver.orders`, 0 orphan `product_id` vs `silver.products`, 0 orphan `seller_id` vs `silver.sellers`. Every line item points to a real order, product and seller.
- Value checks: `price` ranges from 0.85 to 6,735.0. `freight_value` ranges from 0.0 to 409.68. 0 rows with zero or negative price, 0 rows with negative freight. Zero freight was not treated as invalid, since free shipping is plausible. The maximum price of 6,735.0 is a high-value outlier but not impossible, so it was left as is.
- Decision: no cleaning needed, data written to Silver as is. `freight_value` keeps its source name because it matches Olist's own documentation. Gold can alias it as `shipping_cost` if a business-friendly name is needed.
- Note: `freight_value` is the shipping cost charged for the item. `shipping_limit_date` is the seller's deadline to hand the item to the carrier, not a delivery date.
- Final row count: 112,650 in Silver, matching Bronze. Written to `retail_lakehouse.silver.order_items`.