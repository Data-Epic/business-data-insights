# E-Commerce Data Insights & Pipeline

An automated, production-grade data pipeline and analytics warehouse built in Python and PostgreSQL. This project processes over 1 million retail transactions, ensures rigorous data hygiene, and extracts executive-ready insights into revenue trends, regional concentration, product performance, and return risks.

---

## Performance Benchmark: Pandas vs. Alternative Engines

To evaluate processing efficiency across our 1M+ row dataset (`sales.parquet`), we benchmarked wall-clock execution time and peak memory consumption across Pandas, Polars, and DuckDB.

### Benchmark Results
| Engine | Wall-Clock Time (s) | Peak Memory (MB) |
| :--- | :--- | :--- |
| **Pandas** | 0.3460 | 25.93 |
| **Polars** | 0.1559 | 0.02 |
| **DuckDB** | 0.0767 | 0.01 |

### Observations & Tool Selection
DuckDB delivered the fastest execution time (0.0767s) with virtually negligible memory overhead, closely followed by Polars, while Pandas proved noticeably heavier in memory footprint (25.93 MB) and execution duration. Pandas remains ideal for lightweight, exploratory data analysis and workflows requiring rich ecosystem integration. However, for high-throughput production pipelines or multi-gigabyte datasets, switching to vector-based query engines like DuckDB or Polars is recommended to drastically minimize memory pressure and accelerate execution speed.

---

## Getting Started

### 1. Installation & Environment
Ensure you have `uv` installed, then set up your dependencies:
```bash
uv sync

### Testing
uv run pytest -v