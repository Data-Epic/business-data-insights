import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from .extract import PROCESSED_DIR

BASE_DIR = Path(__file__).resolve().parent if "__file__" in locals() else Path.cwd()
CHART_DIR = BASE_DIR.parent / "charts"


# Set a professional global style
sns.set_theme(style="whitegrid")
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.size': 11,
    'axes.labelsize': 12,
    'axes.titlesize': 14,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10
})

def load_data():
    """Load processed datasets."""
    sales_df = pd.read_parquet(PROCESSED_DIR / "sales.parquet")
    customers_df = pd.read_parquet(PROCESSED_DIR / "customers.parquet")
    returns_df = pd.read_parquet(PROCESSED_DIR / "returns.parquet")
    
    # Standardize column naming conventions
    price_col = "price" if "price" in sales_df.columns else "Price"
    qty_col = "quantity" if "quantity" in sales_df.columns else "Quantity"
    date_col = "InvoiceDate" if "InvoiceDate" in sales_df.columns else "invoice_date"
    
    sales_df["revenue"] = sales_df[qty_col] * sales_df[price_col]
    sales_df["invoice_date"] = pd.to_datetime(sales_df[date_col])
    
    return sales_df, customers_df, returns_df

def generate_monthly_revenue_chart(sales_df):
    """Generates and saves the monthly revenue trend chart."""
    sales_df["month_str"] = sales_df["invoice_date"].dt.to_period("M").astype(str)
    monthly_rev = sales_df.groupby("month_str")["revenue"].sum().reset_index()

    fig, ax = plt.subplots(figsize=(10, 5), dpi=300)
    ax.plot(monthly_rev["month_str"], monthly_rev["revenue"] / 1e6, marker='o', color='#1f77b4', linewidth=2.5, markersize=6)
    
    ax.set_title("Monthly Revenue Trajectory & Q4 Holiday Surges", pad=15, fontweight='bold')
    ax.set_xlabel("Month", labelpad=10)
    ax.set_ylabel("Revenue (Millions USD)", labelpad=10)
    plt.xticks(rotation=45)
    plt.tight_layout()

    output_path = CHART_DIR / "monthly_revenue.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path)
    plt.close()
    print(f"Saved: {output_path}")

def generate_top_countries_chart(sales_df, customers_df):
    """Generates and saves the top countries by revenue chart."""
    cust_col = "customer_id" if "customer_id" in sales_df.columns else "CustomerID"
    country_col = "country" if "country" in customers_df.columns else "Country"
    
    merged = sales_df.merge(customers_df, on=cust_col, how="left")
    top_countries = merged.groupby(country_col)["revenue"].sum().sort_values(ascending=False).head(5).reset_index()

    fig, ax = plt.subplots(figsize=(8, 4), dpi=300)
    sns.barplot(data=top_countries, x="revenue", y=country_col, palette="Blues_r", ax=ax)
    
    ax.set_title("Top 5 Countries by Total Revenue", pad=15, fontweight='bold')
    ax.set_xlabel("Revenue (USD)", labelpad=10)
    ax.set_ylabel("Country", labelpad=10)
    plt.tight_layout()

    output_path = CHART_DIR / "top_countries.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path)
    plt.close()
    print(f"Saved: {output_path}")

def generate_top_products_chart(sales_df):
    """Generates and saves the top products by revenue chart."""
    stock_col = "stock_code" if "stock_code" in sales_df.columns else "StockCode"
    top_prods = sales_df.groupby(stock_col)["revenue"].sum().sort_values(ascending=False).head(5).reset_index()

    fig, ax = plt.subplots(figsize=(8, 4), dpi=300)
    sns.barplot(data=top_prods, x="revenue", y=stock_col, palette="viridis", ax=ax)
    
    ax.set_title("Top 5 Products by Revenue", pad=15, fontweight='bold')
    ax.set_xlabel("Revenue (USD)", labelpad=10)
    ax.set_ylabel("Stock Code", labelpad=10)
    plt.tight_layout()

    output_path = CHART_DIR / "top_products.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path)
    plt.close()
    print(f"Saved: {output_path}")


def generate_return_rates_chart(sales_df, returns_df):
    """Generates and saves a chart highlighting top products by return rate."""
    stock_col = "stock_code" if "stock_code" in sales_df.columns else "StockCode"
    
    if stock_col not in returns_df.columns:
        print("Stock code column not found in returns dataframe, skipping return rate chart.")
        return

    ret_counts = returns_df.groupby(stock_col).size().rename("return_count")
    sales_counts = sales_df.groupby(stock_col).size().rename("sales_count")
    prod_returns = pd.concat([sales_counts, ret_counts], axis=1).fillna(0)
    
    # Calculate return rate % and filter for statistical significance (>20 sales)
    prod_returns["return_rate_%"] = (prod_returns["return_count"] / prod_returns["sales_count"]) * 100
    filtered = prod_returns[prod_returns["sales_count"] > 20].sort_values(by="return_rate_%", ascending=False).head(5).reset_index()

    fig, ax = plt.subplots(figsize=(8, 4), dpi=300)
    
    # Use a striking color (e.g., coral/red) to signify risk/returns
    bars = sns.barplot(data=filtered, x="return_rate_%", y=stock_col, palette="Reds_r", ax=ax)
    
    ax.set_title("Highest Return-Rate SKUs (Margin Bleed Risk)", pad=15, fontweight='bold')
    ax.set_xlabel("Return Rate (%)", labelpad=10)
    ax.set_ylabel("Stock Code", labelpad=10)
    
    plt.tight_layout()

    output_path = CHART_DIR / "product_return_rates.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path)
    plt.close()
    print(f"Saved: {output_path}")


def generate_top_volume_products_chart(sales_df):
    """Generates and saves the top products by unit volume chart."""
    stock_col = "stock_code" if "stock_code" in sales_df.columns else "StockCode"
    qty_col = "quantity" if "quantity" in sales_df.columns else "Quantity"
    
    top_vol = sales_df.groupby(stock_col)[qty_col].sum().sort_values(ascending=False).head(5).reset_index()

    fig, ax = plt.subplots(figsize=(8, 4), dpi=300)
    sns.barplot(data=top_vol, x=qty_col, y=stock_col, palette="mako", ax=ax)
    
    ax.set_title("Top 5 Products by Unit Volume (Units Sold)", pad=15, fontweight='bold')
    ax.set_xlabel("Total Units Sold", labelpad=10)
    ax.set_ylabel("Stock Code", labelpad=10)
    plt.tight_layout()

    output_path = CHART_DIR / "top_volume_products.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path)
    plt.close()
    print(f"Saved: {output_path}")



if __name__ == "__main__":
    print("Loading data and generating charts...")
    sales, customers, returns = load_data()
    # generate_monthly_revenue_chart(sales)
    # generate_top_countries_chart(sales, customers)
    # generate_top_products_chart(sales)
    # generate_return_rates_chart(sales, returns)
    generate_top_volume_products_chart(sales)