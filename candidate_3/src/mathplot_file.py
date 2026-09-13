import matplotlib.pyplot as plt
from src.aggregate import (
    revenue_by_month_and_category, top_n_products, top_n_stores,
    month_over_month_growth, warranty_claim_rate_by_category,
)
from src.main import run_pipeline

sales_clean, products_clean, stores_clean, warranty_clean, sales_full = run_pipeline()

# 1. Revenue by month
monthly = month_over_month_growth(sales_full)
plt.figure(figsize=(8, 4))
plt.plot(monthly["sale_year_month"], monthly["revenue"], marker="o")
plt.xticks(rotation=45)
plt.title("Monthly Revenue")
plt.ylabel("Revenue ($)")
plt.tight_layout()
plt.savefig("chart_monthly_revenue.png")
plt.close()

# 2. Top 10 products by revenue
top_products = top_n_products(sales_full)
plt.figure(figsize=(8, 4))
plt.barh(top_products["Product_Name"], top_products["total_revenue"])
plt.title("Top 10 Products by Revenue")
plt.xlabel("Revenue ($)")
plt.tight_layout()
plt.savefig("chart_top_products.png")
plt.close()

# 3. Warranty claim rate by category
claim_rates = warranty_claim_rate_by_category(sales_full, warranty_clean)
plt.figure(figsize=(8, 4))
plt.bar(claim_rates["Category_ID"], claim_rates["claim_rate"])
plt.title("Warranty Claim Rate by Category")
plt.ylabel("Claim Rate")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig("chart_claim_rate.png")
plt.close()

print("Charts saved.")