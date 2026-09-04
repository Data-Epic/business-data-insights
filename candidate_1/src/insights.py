import pandas as pd
from pathlib import Path
from .extract import PROCESSED_DIR

try:
    sales_df = pd.read_parquet(PROCESSED_DIR / "sales.parquet")
    returns_df = pd.read_parquet(PROCESSED_DIR / "returns.parquet")
    customers_df = pd.read_parquet(PROCESSED_DIR / "customers.parquet")

    # Standardize column names
    price_col = "price" if "price" in sales_df.columns else "Price"
    qty_col = "quantity" if "quantity" in sales_df.columns else "Quantity"
    date_col = "InvoiceDate" if "InvoiceDate" in sales_df.columns else "invoice_date"
    stock_col = "stock_code" if "stock_code" in sales_df.columns else "StockCode"
    cust_col = "customer_id" if "customer_id" in sales_df.columns else "CustomerID"
    invoice_col = "Invoice" if "Invoice" in sales_df.columns else "invoice"

    sales_df["revenue"] = sales_df[qty_col] * sales_df[price_col]
    sales_df["invoice_date"] = pd.to_datetime(sales_df[date_col])
    sales_df["month"] = sales_df["invoice_date"].dt.to_period("M")

    print("=== 1. SCALE & DATA QUALITY ===")
    print(f"Total Sales Records: {len(sales_df):,}")
    print(f"Total Returns Records: {len(returns_df):,}")
    print(f"Overall Return Rate: {(len(returns_df) / len(sales_df)) * 100:.2f}%")
    
    valid_sales = set(sales_df["sale_id"]) if "sale_id" in sales_df.columns else set()
    orphaned = len(returns_df[~returns_df["sale_id"].isin(valid_sales)]) if "sale_id" in returns_df.columns and valid_sales else 0
    print(f"Orphaned Returns Handled: {orphaned:,}")

    print("\n=== 2. MONTHLY REVENUE & MoM GROWTH ===")
    monthly_rev = sales_df.groupby("month")["revenue"].sum()
    mom_growth = monthly_rev.pct_change() * 100
    monthly_summary = pd.DataFrame({"Revenue ($)": monthly_rev, "MoM Growth (%)": mom_growth})
    print(monthly_summary)

    print("\n=== 3. TOP COUNTRIES BY REVENUE ===")
    if cust_col in sales_df.columns and cust_col in customers_df.columns:
        merged_cust = sales_df.merge(customers_df, on=cust_col, how="left")
        country_col = "country" if "country" in merged_cust.columns else "Country"
        print(merged_cust.groupby(country_col)["revenue"].sum().sort_values(ascending=False).head(5))

    print("\n=== 4. TOP PRODUCTS BY REVENUE & VOLUME ===")
    print("Top by Revenue:\n", sales_df.groupby(stock_col)["revenue"].sum().sort_values(ascending=False).head(5))
    print("\nTop by Volume (Qty):\n", sales_df.groupby(stock_col)[qty_col].sum().sort_values(ascending=False).head(5))

    print("\n=== 5. ADVANCED BUSINESS METRICS ===")
    # Average Order Value
    aov = sales_df.groupby(invoice_col)["revenue"].sum().mean()
    print(f"Average Order Value (AOV): ${aov:.2f}")

    # Top Products by Return Rate (minimum 20 sales to filter noise)
    if stock_col in returns_df.columns and stock_col in sales_df.columns:
        ret_counts = returns_df.groupby(stock_col).size().rename("return_count")
        sales_counts = sales_df.groupby(stock_col).size().rename("sales_count")
        prod_returns = pd.concat([sales_counts, ret_counts], axis=1).fillna(0)
        prod_returns["return_rate_%"] = (prod_returns["return_count"] / prod_returns["sales_count"]) * 100
        filtered_returns = prod_returns[prod_returns["sales_count"] > 20]
        print("\nTop Products with Highest Return Rates:")
        print(filtered_returns.sort_values(by="return_rate_%", ascending=False).head(5))

except Exception as e:
    print(f"Error running insights script: {e}")