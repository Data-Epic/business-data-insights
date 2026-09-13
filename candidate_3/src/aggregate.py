import pandas as pd


def revenue_by_month_and_category(df: pd.DataFrame) -> pd.DataFrame:
    """Revenue by month and by product category."""
    return (
        df.groupby(["sale_year_month", "Category_ID"], observed=True)["revenue"]
        .sum()
        .reset_index()
        .sort_values(["sale_year_month", "revenue"], ascending=[True, False])
    )


def top_n_products(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Top N products by revenue and volume."""
    return (
        df.groupby(["product_id", "Product_Name"])
        .agg(total_revenue=("revenue", "sum"), total_quantity=("quantity", "sum"))
        .reset_index()
        .sort_values("total_revenue", ascending=False)
        .head(n)
    )


def top_n_stores(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Top N stores by revenue and volume."""
    return (
        df.groupby(["store_id", "Store_Name"])
        .agg(total_revenue=("revenue", "sum"), total_quantity=("quantity", "sum"))
        .reset_index()
        .sort_values("total_revenue", ascending=False)
        .head(n)
    )


def month_over_month_growth(df: pd.DataFrame) -> pd.DataFrame:
    """Month-over-month revenue growth rate."""
    monthly = df.groupby("sale_year_month")["revenue"].sum().reset_index()
    monthly = monthly.sort_values("sale_year_month")
    monthly["prev_revenue"] = monthly["revenue"].shift(1)
    monthly["mom_growth_pct"] = (
        (monthly["revenue"] - monthly["prev_revenue"]) / monthly["prev_revenue"] * 100
    )
    return monthly


def warranty_claim_rate_by_category(sales_products: pd.DataFrame, warranty: pd.DataFrame) -> pd.DataFrame:
    """Claim rate = claims / sales, by product category."""
    claims_per_sale = warranty.groupby("sale_id").size().reset_index(name="claim_count")
    merged = sales_products.merge(claims_per_sale, on="sale_id", how="left")
    merged["claim_count"] = merged["claim_count"].fillna(0)

    summary = (
        merged.groupby("Category_ID", observed=True)
        .agg(total_sales=("sale_id", "count"), total_claims=("claim_count", "sum"))
        .reset_index()
    )
    summary["claim_rate"] = summary["total_claims"] / summary["total_sales"]
    return summary