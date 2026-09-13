import time
from pathlib import Path
from src.extract import read_sales_csv
import polars as pl
from src.extract import raw_dir  # adjust name if yours differs


def benchmark_read_csv() -> None:
    start_time = time.perf_counter()
    df = read_sales_csv()
    end_time = time.perf_counter()

    elapsed_time = end_time - start_time
    print(f"Time taken to read sales.csv: {elapsed_time:.2f} seconds")

    memory_usage = df.memory_usage(deep=True).sum() / (1024 ** 2)
    print(f"Memory usage for sales.csv: {memory_usage:.2f} MB")



def benchmark_pandas_groupby() -> float:
    """Time a groupby-sum aggregation in pandas."""
    df = read_sales_csv()
    start_time = time.perf_counter()
    df.groupby("product_id")["quantity"].sum()
    end_time = time.perf_counter()

    elapsed_time = end_time - start_time
    print(f"[pandas] groupby quantity by product_id: {elapsed_time:.4f} seconds")
    return elapsed_time


def benchmark_polars_groupby() -> float:
    """Same aggregation in Polars. Requires: pip install polars"""
    sales_path = str(raw_dir / "sales.csv")

    start_time = time.perf_counter()
    df = pl.read_csv(sales_path)
    df.group_by("product_id").agg(pl.col("quantity").sum())
    end_time = time.perf_counter()

    elapsed_time = end_time - start_time
    print(f"[polars] read + groupby quantity by product_id: {elapsed_time:.4f} seconds")
    return elapsed_time


if __name__ == "__main__":
    benchmark_read_csv()
    pandas_time = benchmark_pandas_groupby()
    polars_time = benchmark_polars_groupby()
    print(f"Polars was {pandas_time / polars_time:.1f}x the speed of pandas")