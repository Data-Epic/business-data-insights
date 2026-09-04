"""clean.py: Missing value handling, deduplication, schema casting, and parquet serialization."""

from pathlib import Path
import pandas as pd
from .extract import (
    PROCESSED_DIR,
    RAW_DIR,
    read_csv,
    read_json,
    read_parquet,
    write_parquet,
)


def clean_sales(df: pd.DataFrame) -> pd.DataFrame:
    """Cleans transactional sales fact data."""
    # Deduplication
    df = df.drop_duplicates()

    # String standardization
    df["Invoice"] = df["Invoice"].astype(str).str.strip()
    df["StockCode"] = df["StockCode"].astype(str).str.strip().str.upper()

    # Timestamp conversion
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors="coerce")

    # Numeric coercions & positive bounds
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")
    df["Price"] = pd.to_numeric(df["Price"], errors="coerce")
    df = df.dropna(subset=["InvoiceDate", "Quantity", "Price"])
    df = df[(df["Quantity"] > 0) & (df["Price"] > 0)].copy()

    df["Quantity"] = df["Quantity"].astype("int32")
    df["Price"] = df["Price"].astype("float32")

    # Nullable CustomerID handling
    df["CustomerID"] = pd.to_numeric(df["CustomerID"], errors="coerce").astype("Int64")

    # Optional Description harmonization
    if "Description" in df.columns:
        df["Description"] = (
            df["Description"]
            .astype(str)
            .str.strip()
            .str.upper()
            .replace({"NAN": None, "NONE": None, "": None})
        )

    return df


def clean_products(df: pd.DataFrame) -> pd.DataFrame:
    """Cleans product dimension table and picks canonical description per StockCode."""
    df["StockCode"] = df["StockCode"].astype(str).str.strip().str.upper()
    df = df.dropna(subset=["StockCode"])
    df = df[df["StockCode"] != ""]

    if "Description" in df.columns:
        df["Description"] = (
            df["Description"]
            .astype(str)
            .str.strip()
            .str.upper()
            .replace({"NAN": None, "NONE": None, "": None})
        )

    # Keep single unique record per StockCode
    df = df.drop_duplicates(subset=["StockCode"], keep="first")
    return df


def clean_customers(df: pd.DataFrame) -> pd.DataFrame:
    """Cleans customer dimension table."""
    df = df.dropna(subset=["CustomerID"]).copy()
    df["CustomerID"] = pd.to_numeric(df["CustomerID"], errors="coerce")
    df = df[df["CustomerID"] > 0]
    df["CustomerID"] = df["CustomerID"].astype("int64")

    if "Country" in df.columns:
        df["Country"] = df["Country"].astype(str).str.strip().str.title()
        df["Country"] = df["Country"].replace({"Nan": "Unknown", "None": "Unknown", "": "Unknown"})

    df = df.drop_duplicates(subset=["CustomerID"], keep="first")
    return df


def clean_returns(df: pd.DataFrame) -> pd.DataFrame:
    """Cleans returns table and preserves foreign key identifiers."""
    df = df.drop_duplicates()

    df["Invoice"] = df["Invoice"].astype(str).str.strip().str.upper()
    df["StockCode"] = df["StockCode"].astype(str).str.strip().str.upper()
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors="coerce")

    # Cancellation quantities are negative in source logs; store absolute values
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce").abs()
    df["Price"] = pd.to_numeric(df["Price"], errors="coerce")

    df = df.dropna(subset=["InvoiceDate", "Quantity", "Price"])
    df = df[(df["Quantity"] > 0) & (df["Price"] >= 0)].copy()

    df["Quantity"] = df["Quantity"].astype("int32")
    df["Price"] = df["Price"].astype("float32")

    if "sale_id" in df.columns:
        df["sale_id"] = pd.to_numeric(df["sale_id"], errors="coerce").astype("Int64")
    if "CustomerID" in df.columns:
        df["CustomerID"] = pd.to_numeric(df["CustomerID"], errors="coerce").astype("Int64")
    if "return_id" in df.columns:
        df["return_id"] = pd.to_numeric(df["return_id"], errors="coerce").astype("int64")

    return df




def run_cleaning_pipeline():
    # Sales
    raw_sales = read_csv(RAW_DIR / "sales.csv")
    cleaned_sales = clean_sales(raw_sales)
    write_parquet(cleaned_sales, PROCESSED_DIR / "sales.parquet")

    # Products
    raw_products = read_csv(RAW_DIR / "products.csv")
    cleaned_products = clean_products(raw_products)
    write_parquet(cleaned_products, PROCESSED_DIR / "products.parquet")

    # Customers
    raw_customers = read_json(RAW_DIR / "customers.json")
    cleaned_customers = clean_customers(raw_customers)
    write_parquet(cleaned_customers, PROCESSED_DIR / "customers.parquet")

    # Returns
    raw_returns = read_csv(RAW_DIR / "returns.csv")
    cleaned_returns = clean_returns(raw_returns)
    write_parquet(cleaned_returns, PROCESSED_DIR / "returns.parquet")

    # 5. Snapshot read-back verification
    print("\n[VERIFICATION] Reading parquet back:")
    df_check = read_parquet(PROCESSED_DIR / "sales.parquet")
    print(f"sales.parquet shape: {df_check.shape}")
    print(df_check.dtypes)


if __name__ == "__main__":
    run_cleaning_pipeline()