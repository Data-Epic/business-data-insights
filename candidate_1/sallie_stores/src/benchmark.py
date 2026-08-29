from __future__ import annotations

import time
import tracemalloc
from typing import Callable
import logging

import pandas as pd
import polars as pl #type: ignore

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(filename)s:%(funcName)s:%(lineno)d - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def pandas_vs_polars(
    func: Callable[[pd.DataFrame], pd.DataFrame], 
    df: pd.DataFrame, 
    repeats: int = 3
) -> dict[str, float]:
    
    timings: list[float] = []
    peaks: list[float] = []
    for _ in range(repeats):
        tracemalloc.start()
        start = time.perf_counter()
        result = func(df)
        elapsed = time.perf_counter() - start
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        timings.append(elapsed)
        peaks.append(peak / (1024 * 1024))
        if result is None:
            raise ValueError("Benchmark function returned no result.")
    return {
        "avg_seconds": sum(timings) / len(timings),
        "best_seconds": min(timings),
        "avg_memory_mb": sum(peaks) / len(peaks),
    }


def pandas_revenue_by_month(df: pd.DataFrame) -> pd.DataFrame:
    working = df.copy()
    working["revenue"] = working["quantity"] * working["price"]
    working["month"] = working["sale_date"].dt.to_period("M").astype(str)
    return working.groupby("month", as_index=False)["revenue"].sum()    #type:ignore


def polars_revenue_by_month(df: pd.DataFrame) -> pd.DataFrame:
    if pl is None:
        raise ModuleNotFoundError("polars is not installed in the environment.")
    polars_df = pl.from_pandas(df)
    polars_df = polars_df.with_columns(
        [
            (pl.col("quantity") * pl.col("price")).alias("revenue"),
            pl.col("sale_date").dt.to_string("%Y-%m").alias("month"),
        ]
    )
    return polars_df.group_by("month").agg(pl.sum("revenue")).to_pandas()


def benchmark_pandas_vs_polars(
    df: pd.DataFrame, 
    repeats: int = 3
) -> dict[str, dict[str, float]]:

    pandas_result = pandas_vs_polars(pandas_revenue_by_month, df, repeats=repeats)
    polars_result = pandas_vs_polars(polars_revenue_by_month, df, repeats=repeats)
    return {"pandas": pandas_result, "polars": polars_result}


def format_benchmark_markdown(results: dict[str, dict[str, float]]) -> str:
    """Formats benchmark metric dictionaries into an organic, dynamic Markdown table."""
    pandas_avg = results["pandas"]["avg_seconds"]
    polars_avg = results["polars"]["avg_seconds"]

    if pandas_avg < polars_avg:
        speedup = polars_avg / pandas_avg
        pandas_status = f"**{speedup:.2f}x faster**"
        polars_status = "Baseline"
    elif polars_avg < pandas_avg:
        speedup = pandas_avg / polars_avg
        pandas_status = "Baseline"
        polars_status = f"**{speedup:.2f}x faster**"
    else:
        pandas_status = "Identical speed"
        polars_status = "Identical speed"

    lines = [
        "### 📊 Performance Benchmarks: Pandas vs. Polars",
        "",
        "| Engine | Avg Time (s) | Best Time (s) | Peak Memory (MB) | Relative Performance |",
        "| :--- | :--- | :--- | :--- | :--- |",
        f"| **Pandas** | {results['pandas']['avg_seconds']:.4f}s | {results['pandas']['best_seconds']:.4f}s | {results['pandas']['avg_memory_mb']:.2f} MB | {pandas_status} |",
        f"| **Polars** | {results['polars']['avg_seconds']:.4f}s | {results['polars']['best_seconds']:.4f}s | {results['polars']['avg_memory_mb']:.2f} MB | {polars_status} |",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    from pathlib import Path

    project_root = Path(__file__).resolve().parents[1]
    processed_dir = project_root / "data" / "processed"
    sales_df = pd.read_parquet(processed_dir / "sales_enriched.parquet")
    result = benchmark_pandas_vs_polars(sales_df, repeats=3)
    markdown_output = format_benchmark_markdown(result)
    
    logger.info(result)
