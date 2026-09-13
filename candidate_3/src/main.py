"""
main.py
Runs the full pipeline: extract -> clean -> transform -> aggregate -> load to Postgres.

Run: python -m src.main
"""
import os
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv
from src.db import get_connection

from src.extract import read_products_csv, read_sales_csv, read_stores_json, read_warranty_csv
from src.clean import clean_sales, clean_products, clean_stores, clean_warranty
from src.transform import add_date_features, join_sales_products, join_sales_stores
from src.aggregate import (
    revenue_by_month_and_category, top_n_products, top_n_stores,
    month_over_month_growth, warranty_claim_rate_by_category,
)

load_dotenv()


def run_pipeline():
    # ---- extract ----
    sales = read_sales_csv()
    products = read_products_csv()
    stores = read_stores_json()
    warranty = read_warranty_csv()

    # ---- clean ----
    sales_clean = clean_sales(sales)
    products_clean = clean_products(products)
    stores_clean = clean_stores(stores)
    warranty_clean = clean_warranty(warranty)

    # ---- transform ----
    sales_clean = add_date_features(sales_clean)
    sales_products = join_sales_products(sales_clean, products_clean)
    sales_full = join_sales_stores(sales_products, stores_clean)

    # ---- aggregate (prints the 4 required metrics) ----
    print("\n--- Revenue by month/category ---")
    print(revenue_by_month_and_category(sales_full).head(10))

    print("\n--- Top products ---")
    print(top_n_products(sales_full))

    print("\n--- Top stores ---")
    print(top_n_stores(sales_full))

    print("\n--- Month-over-month growth ---")
    print(month_over_month_growth(sales_full))

    print("\n--- Warranty claim rate by category ---")
    print(warranty_claim_rate_by_category(sales_full, warranty_clean))

    return sales_clean, products_clean, stores_clean, warranty_clean, sales_full


def load_to_postgres(sales_clean, products_clean, stores_clean, warranty_clean):
    conn = get_connection()
    cur = conn.cursor()
    # ... rest stays exactly the same

    # products
    for _, row in products_clean.iterrows():
        cur.execute(
            """INSERT INTO products (product_id, product_name, category_id, launch_date, price)
               VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING;""",
            (row["Product_ID"], row["Product_Name"], row["Category_ID"], row["Launch_Date"], row["Price"]),
        )

    # stores
    for _, row in stores_clean.iterrows():
        cur.execute(
            """INSERT INTO stores (store_id, store_name, city, country)
               VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING;""",
            (row["Store_ID"], row["Store_Name"], row["City"], row["Country"]),
        )
    conn.commit()
    print("Products and stores loaded.")

    # sales (bulk)
    sales_records = list(
        sales_clean[["sale_id", "sale_date", "store_id", "product_id", "quantity"]]
        .itertuples(index=False, name=None)
    )
    execute_values(
        cur,
        """INSERT INTO sales (sale_id, sale_date, store_id, product_id, quantity)
           VALUES %s ON CONFLICT DO NOTHING;""",
        sales_records,
        page_size=5000,
    )
    conn.commit()
    print(f"Loaded {len(sales_records)} sales rows.")

    # warranty (bulk)
    warranty_records = list(
        warranty_clean[["claim_id", "sale_id", "claim_date", "repair_status"]]
        .itertuples(index=False, name=None)
    )
    execute_values(
        cur,
        """INSERT INTO warranty (claim_id, sale_id, claim_date, repair_status)
           VALUES %s ON CONFLICT DO NOTHING;""",
        warranty_records,
        page_size=5000,
    )
    conn.commit()
    print(f"Loaded {len(warranty_records)} warranty rows.")

    cur.close()
    conn.close()


if __name__ == "__main__":
    sales_clean, products_clean, stores_clean, warranty_clean, sales_full = run_pipeline()
    load_to_postgres(sales_clean, products_clean, stores_clean, warranty_clean)