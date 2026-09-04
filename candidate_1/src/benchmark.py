"""benchmark.py: Pandas vs Polars vs DuckDB timing and memory benchmarks."""

from pathlib import Path
import time
import tracemalloc
import duckdb
import pandas as pd
import polars as pl

from .extract import PROCESSED_DIR

BASE_DIR = Path(__file__).resolve().parent if "__file__" in locals() else Path.cwd()
PARQUET_FILE = PROCESSED_DIR / "sales.parquet"



def run_pandas(file_path: Path):
    """Pandas aggregation implementation."""
    df = pd.read_parquet(file_path, columns=["StockCode", "Quantity", "Price"])
    df["Revenue"] = df["Quantity"] * df["Price"]
    result = (
        df.groupby("StockCode", as_index=False)
        .agg(TotalRevenue=("Revenue", "sum"), TotalQuantity=("Quantity", "sum"))
        .sort_values(by="TotalRevenue", ascending=False)
        .head(10)
    )
    return result


def run_polars(file_path: Path):
    """Polars aggregation implementation using lazy evaluation."""
    q = (
        pl.scan_parquet(file_path)
        .select(["StockCode", "Quantity", "Price"])
        .with_columns((pl.col("Quantity") * pl.col("Price")).alias("Revenue"))
        .group_by("StockCode")
        .agg([
            pl.col("Revenue").sum().alias("TotalRevenue"),
            pl.col("Quantity").sum().alias("TotalQuantity"),
        ])
        .sort("TotalRevenue", descending=True)
        .limit(10)
    )
    return q.collect()


def run_duckdb(file_path: Path):
    """DuckDB aggregation implementation running direct SQL over Parquet."""
    query = f"""
        SELECT 
            StockCode,
            SUM(Quantity * Price) AS TotalRevenue,
            SUM(Quantity) AS TotalQuantity
        FROM '{file_path}'
        GROUP BY StockCode
        ORDER BY TotalRevenue DESC
        LIMIT 10
    """
    return duckdb.sql(query).df()



def profile_execution(func, *args):
    """Measures wall-clock time (seconds) and peak memory (MB)."""
    tracemalloc.start()
    start_time = time.perf_counter()

    result = func(*args)

    elapsed_time = time.perf_counter() - start_time
    _, peak_mem_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    peak_mem_mb = peak_mem_bytes / (1024 * 1024)
    return result, elapsed_time, peak_mem_mb



def main():
    if not PARQUET_FILE.exists():
        raise FileNotFoundError(f"Missing parquet file: {PARQUET_FILE}")

    print(f"Benchmarking on: {PARQUET_FILE.name}")
    print("=" * 65)
    print(f"{'Engine':<12} | {'Wall-Clock Time (s)':<22} | {'Peak Memory (MB)':<16}")
    print("-" * 65)

    # 1. Pandas
    _, pd_time, pd_mem = profile_execution(run_pandas, PARQUET_FILE)
    print(f"{'Pandas':<12} | {pd_time:<22.4f} | {pd_mem:<16.2f}")

    # 2. Polars
    _, pl_time, pl_mem = profile_execution(run_polars, PARQUET_FILE)
    print(f"{'Polars':<12} | {pl_time:<22.4f} | {pl_mem:<16.2f}")

    # 3. DuckDB
    _, ddb_time, ddb_mem = profile_execution(run_duckdb, PARQUET_FILE)
    print(f"{'DuckDB':<12} | {ddb_time:<22.4f} | {ddb_mem:<16.2f}")
    print("=" * 65)


if __name__ == "__main__":
    main()