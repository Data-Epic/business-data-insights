# data-loading time and memory usage

from pathlib import Path
import pandas as pd

import time


raw_dir = Path(__file__).resolve().parent.parent / "datasets" / "raw"
processed_dir = Path(__file__).resolve().parent.parent / "datasets" / "processed"


def read_products_csv(path: Path = raw_dir / "products.csv") -> pd.DataFrame:
    """Read products CSV file and return a DataFrame."""
    return pd.read_csv(path)


def read_sales_csv(path: Path = raw_dir / "sales.csv") -> pd.DataFrame:
    """Read sales CSV file and return a DataFrame. (1M+ rows)"""
    return pd.read_csv(path)

def read_customers_csv(path: Path = raw_dir / "customers.csv") -> pd.DataFrame:
    """Read customers CSV file and return a DataFrame."""
    return pd.read_csv(path)

def read_warranty_csv(path: Path = raw_dir / "warranty.csv") -> pd.DataFrame:
    """Read warranty CSV file and return a DataFrame."""
    return pd.read_csv(path)

def read_stores_json(path: Path = raw_dir / "stores.json") -> pd.DataFrame:
    """Read stores JSON file and return a DataFrame."""
    return pd.read_json(path)



def write_parquet_snapshot(df: pd.DataFrame, path: Path) -> None:
    """Write a DataFrame to a Parquet file.(Input: DataFrame)"""   # btw, this line is not a comment, it is a docstring. 
    path.parent.mkdir(parents=True, exist_ok=True) #created a folder if it doesn't exist for my processed data
    df.to_parquet(path, index=False)
    print(f"Wrote Parquet snapshot to {path}")

def read_parquet_snapshot(path: Path) -> pd.DataFrame:
    """Read a Parquet file from disk and return it as a DataFrame.(Output: DataFrame)"""
    return pd.read_parquet(path)


def export_stores_to_json(
    csv_path: Path = raw_dir / "stores.csv",
    json_path: Path = raw_dir / "stores.json",
) -> None:
    """One-time helper: convert stores.csv -> stores.json"""
    df = pd.read_csv(csv_path)
    df.to_json(json_path, orient="records")
    print(f"Wrote {len(df)} rows to {json_path}")