# Sallie Stores: Apple Retail Sales ETL and Postgres Pipeline

This project turns a raw Apple Retail Sales dataset into a reusable retail analytics workflow. It reads source files, validates and cleans the records, saves a processed Parquet snapshot, computes business metrics, benchmarks Pandas against Polars, and loads the curated tables into PostgreSQL using a repository layer.

The main questions this project answers are:

- Which products and stores generate the most revenue?
- How does revenue trend by month and category?
- What is the warranty claim rate by category?
- How strong is the month-over-month sales trend?

## Project purpose

This repository is a practical ETL + analytics + database project. The raw files stay in `data/raw`, the cleaned and reusable outputs go into `data/processed`, and the relational database structure lives in `db/schema.sql`.

## Dataset and source files

The project expects these source files in `data/raw`:

- `products.csv`
- `sales.csv`
- `warranty.csv`
- `stores.csv`
- `category.csv`

The `stores.csv` file is also exported to `stores.json` to support the JSON extraction workflow. This gives the project both CSV and JSON ingestion paths.

## Project structure

```text
sallie_stores/
+-- .env
+-- .env.example
+-- README.md
+-- pyproject.toml
+-- data/
|   +-- raw/
|   |   +-- category.csv
|   |   +-- products.csv
|   |   +-- sales.csv
|   |   +-- stores.csv
|   |   +-- stores.json
|   |   +-- warranty.csv
|   +-- processed/
|       +-- categories.parquet
|       +-- products.parquet
|       +-- sales.parquet
|       +-- stores.parquet
|       +-- warranty.parquet
|       +-- sales_enriched.parquet
+-- db/
|   +-- schema.sql
+-- src/
|   +-- __init__.py
|   +-- extract.py
|   +-- clean.py
|   +-- transform.py
|   +-- aggregate.py
|   +-- benchmark.py
|   +-- db.py
|   +-- load.py
|   +-- repository.py
+-- tests/
|   +-- test_repository.py
+-- slides/
```

## Script relationships and responsibilities

The scripts are meant to work together as one pipeline:

1. `src/extract.py`
   - Reads raw CSV and JSON files
   - Validates file existence
   - Converts `stores.csv` into `stores.json` when needed
   - Loads the raw bundle for the rest of the pipeline

2. `src/clean.py`
   - Standardizes column names
   - Strips whitespace and normalizes casing
   - Converts date and numeric values
   - Removes duplicates and invalid rows
   - Drops impossible values such as zero or negative prices/quantities

3. `src/transform.py`
   - Runs the cleaning workflow
   - Saves processed outputs to `data/processed` as Parquet files
   - Produces `sales_enriched.parquet` with revenue and month fields
   - Creates the reusable, downstream-ready dataset layer

4. `src/aggregate.py`
   - Computes revenue by month and category
   - Identifies top products and stores by revenue
   - Calculates warranty claim rate by category
   - Builds month-over-month growth metrics

5. `src/benchmark.py`
   - Runs the same revenue aggregation in Pandas and Polars
   - Tracks timing and memory footprint
   - Gives a clear engine performance comparison for the project narrative

6. `src/db.py`
   - Reads `.env` settings
   - Opens the PostgreSQL connection
   - Supplies schema-application utilities

7. `src/load.py`
   - Loads the raw bundle, cleans it, and writes it to PostgreSQL
   - Applies the schema from `db/schema.sql`
   - Inserts rows by table with resume and batch control options

8. `src/repository.py`
   - Encapsulates insert operations and SQL queries
   - Handles parameterized inserts and analytic read queries
   - Powers DB writes and reporting logic for the project

## Recommended pipeline flow

```text
raw files -> extract -> clean -> transform -> processed parquet
                                      |
                                      +-> aggregate insights
                                      +-> benchmark engine performance
                                      +-> load to PostgreSQL via repository
```

## Requirements

- Python 3.14+
- Poetry
- PostgreSQL running locally
- A database such as `sallie_stores_db` or your own chosen name

## Setup

From the project root:

```powershell
poetry install
```

If you have not already created a local `.env`, copy the example and update it:

```powershell
Copy-Item .env.example .env
```

Then edit `.env` to match your local database credentials:

```dotenv
DB_NAME=sallie_stores_db
DB_USER=postgres
DB_PASSWORD=your_password_here
DB_HOST=localhost
DB_PORT=5432
```

## Create the database

Create the PostgreSQL database if it does not exist yet:

```powershell
psql -h localhost -U postgres -c "CREATE DATABASE sallie_stores_db;"
```

If you use a different database name, keep it aligned with the value in `.env`.

## Apply the schema

Run the schema file before loading data:

```powershell
psql -h localhost -U postgres -d sallie_stores_db -f db/schema.sql
```

## CLI flags and usage

The main loader supports flags for targeted loading and operational control. These are defined in `src/load.py`.

### Supported flags

```powershell
poetry run python -m src.load --help
```

Available flags:

- `--tables`: load specific tables only. Example:

  ```powershell
  poetry run python -m src.load --tables sales products warranty
  ```

- `--resume`: enable resume mode. This is the default behavior.

  ```powershell
  poetry run python -m src.load --resume
  ```

- `--no-resume`: start from the beginning without any checkpoint resume behavior.

  ```powershell
  poetry run python -m src.load --no-resume
  ```

- `--batch-size`: set the row batch size used during inserts. Example:

  ```powershell
  poetry run python -m src.load --batch-size 2000
  ```

### Typical load commands

Full load (default settings):

```powershell
poetry run python -m src.load
```

Load only selected tables:

```powershell
poetry run python -m src.load --tables sales stores products
```

Reload from scratch with smaller inserts:

```powershell
poetry run python -m src.load --no-resume --batch-size 5000
```

## Run the ETL pipeline

### 1) Extract and create the JSON export

This step reads the raw files and creates `stores.json` if it is missing:

```powershell
poetry run python -m src.extract
```

### 2) Clean and transform data

This step cleans every table and writes the processed Parquet files into `data/processed`:

```powershell
poetry run python -m src.transform
```

### 3) Load data to PostgreSQL

This applies the schema and inserts the cleaned tables into the database:

```powershell
poetry run python -m src.load
```

### 4) Run analytics directly

You can compute summary metrics from the processed Parquet files:

```powershell
poetry run python -c "from src.aggregate import compute_summary_metrics; from src.extract import BaseDataLoader; sales = BaseDataLoader.read_parquet('data/processed/sales.parquet'); products = BaseDataLoader.read_parquet('data/processed/products.parquet'); stores = BaseDataLoader.read_parquet('data/processed/stores.parquet'); warranty = BaseDataLoader.read_parquet('data/processed/warranty.parquet'); print(compute_summary_metrics(sales, products, stores, warranty).keys())"
```

### 5) Benchmark Pandas vs Polars

This compares the same revenue aggregation in both engines:

```powershell
poetry run python -c "from src.benchmark import benchmark_pandas_vs_polars; from src.extract import BaseDataLoader; df = BaseDataLoader.read_parquet('data/processed/sales_enriched.parquet'); print(benchmark_pandas_vs_polars(df, repeats=3))"
```

## Repository and query layer

The repository pattern keeps SQL and data access separate from the ETL layer. It is the interface used for DB writes and read queries.

Example:

```python
from src.db import get_connection
from src.repository import SalesRepository

conn = get_connection()
repo = SalesRepository(conn)

print(repo.fetch_top_products_per_store(5))
print(repo.fetch_warranty_claim_rate_by_category())

conn.close()
```

This repository is intended to support downstream reporting from the PostgreSQL database.

## Tests

Run the test suite:

```powershell
poetry run python -m pytest -q
```

The project includes repository and foreign-key validation checks in `tests/test_repository.py`.

## Data-quality decisions

The cleaning logic deliberately handles recurring issues in raw retail data:

- whitespace and capitalization inconsistencies in identifiers and labels
- missing values in numeric and date fields
- duplicate rows by business key such as `sale_id` and `product_id`
- invalid values like zero/negative quantities and prices
- date conversion using `pd.to_datetime` with explicit parsing

This ensures the processed output is suitable for both analytics and relational loading.

## Slide deck preparation advice

If this project is being presented as a business case or technical demo, keep the story simple and outcome-led.

### Best structure for the deck

1. Title slide
   - Project name, scope, and date
   - One sentence: “Built an ETL + analytics + Postgres pipeline for Apple retail sales data.”

2. Business problem and objective
   - Explain why this dataset matters to retail analytics
   - State the questions the project is trying to answer
   - Keep this slide short and executive-friendly

3. Data pipeline architecture
   - Show the journey from raw files to cleaned Parquet to database tables
   - Use a simple flow diagram with 4-5 boxes
   - This is the key technical slide and should be easy to read in 10 seconds

4. Data cleaning and quality decisions
   - Highlight the types of issues fixed: duplicates, nulls, bad dates, invalid quantities/prices
   - Show a few numbers or examples instead of dumping all logic
   - This gives credibility to the ETL work

5. Key analytics outputs
   - Revenue by month
   - Revenue by category
   - Top stores/products by revenue
   - Warranty claim rate by category
   - Keep visuals clear and avoid too many tables

6. Database / repository layer
   - Show the schema relationship: categories → products → sales → warranty
   - Explain that the database model supports relational queries and reporting
   - This is where the project becomes more than a notebook or script

7. Performance benchmark
   - Show the Pandas vs Polars summary in a compact table
   - Explain what matters: speed, memory, and fit-for-purpose usage
   - Keep the interpretation honest and business-relevant

8. Final outcome and recommendations
   - Summarize the result: cleaned data, reusable processed outputs, and PostgreSQL-ready analytics
   - End with a short recommendation for next steps, such as dashboarding or deeper product forecasting

### Presentation advice

- Use one key point per slide.
- Prefer screenshots of the actual outputs over raw code blocks.
- Use 3-5 metrics in the final deck, not every metric produced by the project.
- Keep code snippets minimal; the story is the product, not the implementation details.
- If you show the loader flags, explain them in plain business language: “select tables,” “resume,” and “batch size.”
- For a stakeholder audience, lead with business insight and only move into technical details when asked.

### Suggested deck length

- 6-8 slides is ideal for a concise demo
- 10-12 slides is acceptable for a technical review
- Keep a 3-5 minute verbal walkthrough if you are presenting live

A strong deck should tell this story:

> We ingested raw Apple retail sales data, fixed the quality issues, built a reusable processed layer, generated meaningful business metrics, and prepared the data for relational reporting and analytics.

## Notes about the process

- The processed Parquet files are reusable and should be treated as the canonical cleaned snapshot.
- It is expected that `stores.json` is generated from the raw store dimension instead of reading a custom lookup file.
- The repository layer uses parameterized SQL to avoid unsafe string interpolation and to support DB-integrity checks.

## Typical full run

```powershell
poetry install
Copy-Item .env.example .env
# edit .env with your local DB credentials
psql -h localhost -U postgres -c "CREATE DATABASE sallie_stores_db;"
psql -h localhost -U postgres -d sallie_stores_db -f db/schema.sql
poetry run python -m src.extract
poetry run python -m src.transform
poetry run python -m src.load
poetry run python -m pytest -q
```

That is the standard end-to-end workflow for this project.
