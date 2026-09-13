# business-data-insights-



# Business Data Insights Pipeline

A Python data pipeline that extracts, cleans, transforms, and aggregates Apple Retail Sales data (synthetic Kaggle dataset), benchmarks Pandas against Polars, and loads curated results into PostgreSQL.

## What it does

- **Extracts** data from CSV (`products.csv`, `sales.csv`, `warranty.csv`) and JSON (`stores.json`, exported from `stores.csv`)
- **Writes/reads a Parquet snapshot** of cleaned sales data
- **Cleans** each dataset: drops duplicates, handles missing values, fixes dtypes (dates, numeric types, `category` dtype for low-cardinality text)
- **Transforms**: engineers date features (year, month, day-of-week) and joins sales with products/stores to compute revenue
- **Aggregates** four business metrics:
  - Revenue by month and category
  - Top products/stores by revenue and volume
  - Warranty claim rate by category
  - Month-over-month revenue growth
- **Benchmarks** Pandas vs. Polars on a groupby aggregation
- **Loads** cleaned data into PostgreSQL via a schema with primary/foreign keys and constraints
- **Tests** cleaning logic and database constraints (foreign key + check violations)

## Project structure

```
src/
├── extract.py       # CSV/JSON/Parquet I/O
├── clean.py          # duplicates, missing values, dtype fixes
├── transform.py       # date features, joins, revenue calc
├── aggregate.py       # the 4 business metrics
├── benchmark.py        # Pandas vs Polars timing
├── db.py             # Postgres connection management
├── main.py            # orchestrates the full pipeline
db/
└── schema.sql        # DDL: tables, keys, constraints
tests/
├── test_pipeline.py     # cleaning logic tests
└── test_repository.py    # DB constraint tests
```

## Setup

1. Install dependencies:
   ```bash
   python -m pip install pandas polars psycopg2-binary python-dotenv pytest pyarrow matplotlib
   ```

2. Copy `.env.example` to `.env` and fill in your Postgres credentials.

3. Create the database and apply the schema:
   ```bash
   psql -U postgres -d your_db_name -f db/schema.sql
   ```
   (or run `db/schema.sql` in pgAdmin's Query Tool)

## Running the pipeline

```bash
python -m src.main
```

This runs extraction → cleaning → transformation → prints all four aggregate metrics → loads data into Postgres.

## Running tests

```bash
python -m pytest tests/ -v
```

## Pandas vs. Polars

Loading `sales.csv` (1M+ rows) took ~12.2s in Pandas (66 MB memory). A groupby-sum on `quantity` by `product_id` took 0.87s in Pandas vs. 0.34s in Polars (~2.5x faster), thanks to Polars' multi-threaded, columnar execution engine vs. Pandas' single-threaded default. Pandas remains the better choice for smaller datasets and quick exploratory work; Polars is worth reaching for once dataset size or aggregation complexity starts to slow Pandas down.

## Data notes

This is a **synthetic dataset** (Apple Retail Sales, Kaggle) — cleaning steps found no duplicates or missing values in practice, though the cleaning logic was verified by manually injecting invalid rows and confirming they were correctly dropped.

## Status

- Extraction, Parquet round-trip, cleaning, transformation, aggregation
- Pandas vs. Polars benchmark
- Postgres schema, load, and both required SQL queries (window function + CTE)
- Tests passing (pipeline logic + DB constraints)
- Slide deck in progress






# Notes
Parquet is a binary, columnar format that:

Stores actual typed data (an integer is stored as an integer, not text), so reading it back is faster and doesn't require re-guessing dtypes.
Stores data column-by-column rather than row-by-row — so if you only need one column, tools can skip reading the others entirely (this is why DuckDB was fast in your upcoming Polars/DuckDB comparison).
Compresses much smaller than CSV for the same data. 

Note( CSV is a text format — every number, every date, is stored as literal characters, like "1149" 
instead of the actual number 1149. Every time you read a CSV, pandas has to re-guess and re-parse every column's type from scratch.)


pyarrow is the same columnar format both Polars and DuckDB read natively, 
which is part of why Parquet plays so well with those tools.

