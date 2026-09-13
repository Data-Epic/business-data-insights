import pandas as pd


def clean_sales(df: pd.DataFrame) -> pd.DataFrame:
    """Copy, drop duplicate rows, drop missing required fields, parse dates, fix quantity."""
    df = df.copy()

    before = len(df)
    df_cleaned = df.drop_duplicates(subset=["sale_id"])
    print(f"Removed {before - len(df_cleaned)} duplicate rows from sales data.")

    before = len(df_cleaned)
    df_no_missing = df_cleaned.dropna(subset=["quantity", "sale_date", "store_id", "product_id"])
    print(f"Removed {before - len(df_no_missing)} rows with missing required fields.")

    df_no_missing["sale_date"] = pd.to_datetime(
        df_no_missing["sale_date"], format="%d-%m-%Y", errors="coerce"
    )

    before = len(df_no_missing)
    df_cleaned_date = df_no_missing.dropna(subset=["sale_date"])
    print(f"Removed {before - len(df_cleaned_date)} rows with unparseable dates.")

    df_cleaned_date["quantity"] = pd.to_numeric(df_cleaned_date["quantity"], errors="coerce")

    before = len(df_cleaned_date)
    df_valid_qty = df_cleaned_date.dropna(subset=["quantity"])
    df_valid_qty = df_valid_qty[df_valid_qty["quantity"] > 0]
    print(f"Removed {before - len(df_valid_qty)} rows with invalid/non-positive quantity.")

    return df_valid_qty


def clean_products(df: pd.DataFrame) -> pd.DataFrame:
    """Copy, drop duplicates, drop missing required fields, fix dtypes."""
    df = df.copy()

    before = len(df)
    df_cleaned = df.drop_duplicates(subset=["Product_ID"])
    print(f"Removed {before - len(df_cleaned)} duplicate products.")

    before = len(df_cleaned)
    df_no_missing = df_cleaned.dropna(subset=["Product_ID", "Product_Name", "Price"])
    print(f"Removed {before - len(df_no_missing)} rows with missing required fields.")

    df_no_missing["Category_ID"] = df_no_missing["Category_ID"].astype("category")
    df_no_missing["Launch_Date"] = pd.to_datetime(df_no_missing["Launch_Date"], errors="coerce")

    df_no_missing["Price"] = pd.to_numeric(df_no_missing["Price"], errors="coerce")
    before = len(df_no_missing)
    df_valid = df_no_missing.dropna(subset=["Price"])
    df_valid = df_valid[df_valid["Price"] > 0]
    print(f"Removed {before - len(df_valid)} rows with invalid price.")

    return df_valid






def clean_stores(df: pd.DataFrame) -> pd.DataFrame:
    """Copy, drop duplicates, drop missing required fields, fix dtypes."""
    df = df.copy()

    before = len(df)
    df_cleaned = df.drop_duplicates(subset=["Store_ID"])
    print(f"Removed {before - len(df_cleaned)} duplicate stores.")

    before = len(df_cleaned)
    df_no_missing = df_cleaned.dropna(subset=["Store_ID", "Store_Name"])
    print(f"Removed {before - len(df_no_missing)} rows with missing required fields.")

    # City/Country repeat across many stores -> category dtype saves memory
    df_no_missing["City"] = df_no_missing["City"].astype("category")
    df_no_missing["Country"] = df_no_missing["Country"].astype("category")

    return df_no_missing



def clean_warranty(df: pd.DataFrame) -> pd.DataFrame:
    """Copy, drop duplicates, drop missing required fields, parse dates."""
    df = df.copy()

    before = len(df)
    df_cleaned = df.drop_duplicates(subset=["claim_id"])
    print(f"Removed {before - len(df_cleaned)} duplicate warranty claims.")

    before = len(df_cleaned)
    df_no_missing = df_cleaned.dropna(subset=["claim_id", "sale_id"])
    print(f"Removed {before - len(df_no_missing)} rows with missing required fields.")

    df_no_missing["claim_date"] = pd.to_datetime(df_no_missing["claim_date"], errors="coerce")

    # repair_status is low-cardinality text (e.g. a handful of status values) -> category dtype
    df_no_missing["repair_status"] = df_no_missing["repair_status"].astype("category")

    return df_no_missing