import pandas as pd


def add_date_features(sales: pd.DataFrame) -> pd.DataFrame:
    """Engineer year/month/day-of-week from sale_date."""
    df = sales.copy()
    df["sale_year"] = df["sale_date"].dt.year
    df["sale_month"] = df["sale_date"].dt.month
    df["sale_year_month"] = df["sale_date"].dt.to_period("M").astype(str)  # e.g. "2022-07"
    df["sale_dayofweek"] = df["sale_date"].dt.day_name()
    return df


def join_sales_products(sales: pd.DataFrame, products: pd.DataFrame) -> pd.DataFrame:
    """Merge sales with products to get Price/Category_ID, then compute revenue."""
    merged = sales.merge(
        products[["Product_ID", "Product_Name", "Category_ID", "Price"]],
        left_on="product_id",
        right_on="Product_ID",
        how="left",
    )
    merged["revenue"] = merged["quantity"] * merged["Price"]
    return merged


def join_sales_stores(sales: pd.DataFrame, stores: pd.DataFrame) -> pd.DataFrame:
    """Merge sales with stores to get City/Country."""
    merged = sales.merge(
        stores, left_on="store_id", right_on="Store_ID", how="left"
    )
    return merged