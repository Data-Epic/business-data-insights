"""transform.py: Filtering, date features, and derived metrics."""

from pathlib import Path
import pandas as pd
from .extract import read_parquet, PROCESSED_DIR




def enrich_sales(sales_df: pd.DataFrame, customers_df: pd.DataFrame) -> pd.DataFrame:
    """Filters data, creates date features, computes line revenue, and attaches dimensions."""
    df = sales_df.copy()

    # 1. Derived Financial Metrics
    df["Revenue"] = df["Quantity"] * df["Price"]

    # 2. Date & Time Features
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])
    df["Year"] = df["InvoiceDate"].dt.year
    df["Month"] = df["InvoiceDate"].dt.month
    df["YearMonth"] = df["InvoiceDate"].dt.to_period("M")
    df["DayOfWeek"] = df["InvoiceDate"].dt.day_name()
    df["Hour"] = df["InvoiceDate"].dt.hour

    # 3. Join Customer Dimension (Country attribute)
    if "Country" not in df.columns and "CustomerID" in customers_df.columns:
        cust_lookup = customers_df[["CustomerID", "Country"]].drop_duplicates(subset=["CustomerID"])
        df = df.merge(cust_lookup, on="CustomerID", how="left")
        df["Country"] = df["Country"].fillna("Unknown")

    return df


def enrich_products(products_df: pd.DataFrame) -> pd.DataFrame:
    """Categorizes products using description prefixes/heuristics."""
    df = products_df.copy()

    # Simple category heuristic based on common high-frequency retail terms
    def assign_category(desc: str) -> str:
        if not isinstance(desc, str):
            return "OTHER"
        desc = desc.upper()
        if any(w in desc for w in ["HEART", "STAR", "HANGING"]):
            return "DECORATION"
        if any(w in desc for w in ["BAG", "TOTE", "LUNCH"]):
            return "BAGS"
        if any(w in desc for w in ["MUG", "CUP", "PLATE", "BOWL", "TEAPOT"]):
            return "KITCHEN & DINING"
        if any(w in desc for w in ["LIGHT", "LANTERN", "CANDLE", "HOLDER"]):
            return "LIGHTING"
        if any(w in desc for w in ["BOX", "DRAWER", "TIN"]):
            return "STORAGE"
        return "GENERAL"

    df["Category"] = df["Description"].apply(assign_category)
    return df


def get_analytical_dataset() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Reads cleaned parquet files and outputs transformed analytical frames."""
    raw_sales = read_parquet(PROCESSED_DIR / "sales.parquet")
    raw_customers = read_parquet(PROCESSED_DIR / "customers.parquet")
    raw_products = read_parquet(PROCESSED_DIR / "products.parquet")
    raw_returns = read_parquet(PROCESSED_DIR / "returns.parquet")

    sales_enriched = enrich_sales(raw_sales, raw_customers)
    products_enriched = enrich_products(raw_products)

    # Attach Product Category to Sales
    sales_enriched = sales_enriched.merge(
        products_enriched[["StockCode", "Category"]], on="StockCode", how="left"
    )
    sales_enriched["Category"] = sales_enriched["Category"].fillna("GENERAL")

    return sales_enriched, products_enriched, raw_returns


if __name__ == "__main__":
    sales, products, returns = get_analytical_dataset()
    print(f"Enriched sales shape: {sales.shape}")
    print(sales[["Invoice", "YearMonth", "Revenue", "Country", "Category"]].head())