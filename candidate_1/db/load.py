import io
import traceback
from pathlib import Path
import pandas as pd
from .db_config import engine
from src.extract import PROCESSED_DIR
from sqlalchemy import text


def copy_df_to_postgres(df: pd.DataFrame, table_name: str, connection):
    """Executes high-throughput streaming bulk COPY from Pandas DataFrame."""

    buffer = io.StringIO()
    df.to_csv(buffer, index=False, header=False, sep="\t", na_rep="\\N")
    buffer.seek(0)

    raw_conn = connection.connection  # underlying DB-API psycopg2 connection
    columns = [f'"{col}"' for col in df.columns]
    sql = f"COPY {table_name} ({', '.join(columns)}) FROM STDIN WITH (FORMAT text, DELIMITER '\t', NULL '\\N')"

    with raw_conn.cursor() as cursor:
        cursor.copy_expert(sql=sql, file=buffer)


def load_parquet_to_dw():
    # Break into separate transactions so early successes aren't rolled back
    
    with engine.connect() as conn:
        try:
            print("Truncating existing tables for a clean load...")
            with conn.begin():
                # CASCADE automatically handles foreign key dependencies during truncation
                conn.execute(text("TRUNCATE TABLE returns, sales, customers, products CASCADE;"))
            print("Tables truncated successfully.")
        except Exception as e:
            print(f"\n❌ FAILED truncating tables: {e}")
            traceback.print_exc()
            return
        
        # 1. Load Products
        try:
            print("Bulk loading products...")
            with conn.begin():
                p_df = pd.read_parquet(PROCESSED_DIR / "products.parquet")
                p_df = p_df.rename(columns={"StockCode": "stock_code", "Description": "description"})
                copy_df_to_postgres(p_df[["stock_code", "description"]], "products", conn)
            print("Products loaded successfully.")
        except Exception as e:
            print(f"\n❌ FAILED loading products: {e}")
            return

        # 2. Load Customers
        try:
            print("Bulk loading customers...")
            with conn.begin():
                c_df = pd.read_parquet(PROCESSED_DIR / "customers.parquet")
                c_df = c_df.rename(columns={"CustomerID": "customer_id", "Country": "country"})
                copy_df_to_postgres(c_df[["customer_id", "country"]], "customers", conn)
            print("Customers loaded successfully.")
        except Exception as e:
            print(f"\n❌ FAILED loading customers: {e}")
            return

        # 3. Load Sales
        try:
            print("Bulk loading sales (1,000,000+ records)...")
            with conn.begin():
                s_df = pd.read_parquet(PROCESSED_DIR / "sales.parquet")
                s_df = s_df.rename(columns={
                    "sale_id": "sale_id",
                    "Invoice": "invoice",
                    "StockCode": "stock_code",
                    "CustomerID": "customer_id",
                    "Quantity": "quantity",
                    "Price": "price",
                    "InvoiceDate": "invoice_date",
                })
                copy_df_to_postgres(s_df[["sale_id", "invoice", "stock_code", "customer_id", "quantity", "price", "invoice_date"]], "sales", conn)
            print("Sales loaded successfully.")
        except Exception as e:
            print(f"\n❌ FAILED loading sales: {e}")
            traceback.print_exc()
            return

        # 4. Load Returns
        try:
            print("Bulk loading returns...")
            with conn.begin():
                r_df = pd.read_parquet(PROCESSED_DIR / "returns.parquet")
                r_df = r_df.rename(columns={
                    "return_id": "return_id",
                    "sale_id": "sale_id",
                    "Invoice": "invoice",
                    "StockCode": "stock_code",
                    "CustomerID": "customer_id",
                    "Quantity": "quantity",
                    "Price": "price",
                    "InvoiceDate": "invoice_date",
                })
                
                # 1. Get the exact set of valid sale_ids that were just loaded
                valid_sale_ids = set(s_df["sale_id"])
                
                # 2. If a return's sale_id isn't in the sales table, set it to None
                r_df["sale_id"] = r_df["sale_id"].apply(
                    lambda x: x if pd.notna(x) and x in valid_sale_ids else None
                )
                
                # Force pandas to use Nullable Integers so "246.0" becomes "246"
                r_df["sale_id"] = pd.to_numeric(r_df["sale_id"]).astype("Int64")
                
                if "customer_id" in r_df.columns:
                    r_df["customer_id"] = pd.to_numeric(r_df["customer_id"]).astype("Int64")

                copy_df_to_postgres(
                    r_df[["return_id", "sale_id", "invoice", "stock_code", "customer_id", "quantity", "price", "invoice_date"]], 
                    "returns", 
                    conn
                )
            print("Returns loaded successfully.")
        except Exception as e:
            print(f"\n❌ FAILED loading returns: {e}")
            traceback.print_exc()
            return    

    print("\n✅ All Parquet data successfully loaded into PostgreSQL.")

if __name__ == "__main__":
    load_parquet_to_dw()