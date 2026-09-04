"""aggregate.py: Grouping and business aggregation metrics."""

import pandas as pd
from .transform import get_analytical_dataset




def get_revenue_by_month_and_country(sales_df: pd.DataFrame) -> pd.DataFrame:
    """Computes total revenue broken down by YearMonth and Country."""
    monthly_country_rev = (
        sales_df.groupby(["YearMonth", "Country"], as_index=False)["Revenue"]
        .sum()
        .sort_values(["YearMonth", "Revenue"], ascending=[True, False])
    )
    return monthly_country_rev



def get_top_entities(sales_df: pd.DataFrame, n: int = 10) -> dict[str, pd.DataFrame]:
    """Computes Top N Products and Customers ranked by Revenue and by Volume."""
    # Top Products
    top_products_rev = (
        sales_df.groupby(["StockCode"], as_index=False)
        .agg(TotalRevenue=("Revenue", "sum"), TotalQuantity=("Quantity", "sum"))
        .sort_values(by="TotalRevenue", ascending=False)
        .head(n)
    )

    top_products_vol = (
        sales_df.groupby(["StockCode"], as_index=False)
        .agg(TotalQuantity=("Quantity", "sum"), TotalRevenue=("Revenue", "sum"))
        .sort_values(by="TotalQuantity", ascending=False)
        .head(n)
    )

    # Top Customers (filter null guests)
    valid_customers = sales_df.dropna(subset=["CustomerID"]).copy()
    valid_customers["CustomerID"] = valid_customers["CustomerID"].astype(int)

    top_customers_rev = (
        valid_customers.groupby("CustomerID", as_index=False)
        .agg(TotalSpend=("Revenue", "sum"), TotalItems=("Quantity", "sum"))
        .sort_values(by="TotalSpend", ascending=False)
        .head(n)
    )

    return {
        "top_products_by_revenue": top_products_rev,
        "top_products_by_volume": top_products_vol,
        "top_customers_by_revenue": top_customers_rev,
    }



def get_return_rates(
    sales_df: pd.DataFrame, returns_df: pd.DataFrame, min_sales_threshold: int = 100
) -> pd.DataFrame:
    """Computes return rates (Returned Quantity / Sold Quantity) by product."""
    # Aggregate sales volume
    sales_vol = sales_df.groupby("StockCode")["Quantity"].sum().rename("UnitsSold")

    # Aggregate return volume
    returns_vol = returns_df.groupby("StockCode")["Quantity"].sum().rename("UnitsReturned")

    # Merge and calculate return rate
    rates_df = pd.concat([sales_vol, returns_vol], axis=1).fillna(0)
    # Filter items with significant sales volume to prevent small-sample bias
    rates_df = rates_df[rates_df["UnitsSold"] >= min_sales_threshold].copy()

    rates_df["ReturnRatePercent"] = (rates_df["UnitsReturned"] / rates_df["UnitsSold"]) * 100
    rates_df = rates_df.sort_values(by="ReturnRatePercent", ascending=False).reset_index()

    return rates_df



def get_mom_revenue_growth(sales_df: pd.DataFrame) -> pd.DataFrame:
    """Computes total monthly revenue and month-over-month % growth."""
    monthly = (
        sales_df.groupby("YearMonth")["Revenue"]
        .sum()
        .reset_index()
        .sort_values("YearMonth")
    )
    # Calculate previous month revenue and percentage difference
    monthly["PriorMonthRevenue"] = monthly["Revenue"].shift(1)
    monthly["MoM_GrowthRate"] = (
        (monthly["Revenue"] - monthly["PriorMonthRevenue"]) / monthly["PriorMonthRevenue"]
    ) * 100

    return monthly




def run_aggregations():
    sales, products, returns = get_analytical_dataset()

    print("=" * 60)
    print("1. REVENUE BY MONTH & COUNTRY (Top Sample)")
    print("=" * 60)
    rev_by_month_country = get_revenue_by_month_and_country(sales)
    print(rev_by_month_country.head(10).to_string(index=False))

    print("\n" + "=" * 60)
    print("2. TOP 5 PRODUCTS BY REVENUE")
    print("=" * 60)
    top_entities = get_top_entities(sales, n=5)
    print(top_entities["top_products_by_revenue"].to_string(index=False))

    print("\n" + "=" * 60)
    print("3. TOP 5 PRODUCTS BY RETURN RATE (Min 100 sales)")
    print("=" * 60)
    return_rates = get_return_rates(sales, returns)
    print(return_rates.head(5).to_string(index=False))

    print("\n" + "=" * 60)
    print("4. MONTH-OVER-MONTH REVENUE GROWTH")
    print("=" * 60)
    mom_growth = get_mom_revenue_growth(sales)
    print(mom_growth.to_string(index=False))


if __name__ == "__main__":
    run_aggregations()