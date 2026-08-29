from __future__ import annotations
from pathlib import Path
import logging
import pandas as pd

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(filename)s:%(funcName)s:%(lineno)d - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    cleaned = df.copy()
    cleaned.columns = [str(col).strip().lower() for col in cleaned.columns]
    return cleaned


def clean_categories(df: pd.DataFrame) -> pd.DataFrame:
    df = normalize_columns(df)
    df["category_id"] = df.get("category_id", "").astype(str).str.strip()   #type: ignore
    df["category_name"] = df.get("category_name", "").astype(str).str.strip()   #type: ignore
    df = df[(df["category_id"] != "") & (df["category_name"] != "")]    #type: ignore
    df = df.dropna(subset=["category_id", "category_name"]).drop_duplicates(
        subset=["category_id"]
    )
    return df.reset_index(drop=True)


def clean_products(df: pd.DataFrame) -> pd.DataFrame:
    df = normalize_columns(df)
    required = ["product_id", "product_name", "category_id", "price"]
    for col in required:
        if col not in df.columns:
            raise KeyError(f"Missing required column in products data: {col}")

    df["product_id"] = df["product_id"].astype(str).str.strip() #type: ignore
    df["product_name"] = df["product_name"].astype(str).str.strip() #type: ignore
    df["category_id"] = df["category_id"].astype(str).str.strip()   #type: ignore
    
    if "launch_date" in df.columns:
        df["launch_date"] = pd.to_datetime(df["launch_date"], errors="coerce")
    
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df = df[df["price"] > 0]    #type: ignore
    
    df = df.dropna(
        subset=["product_id", "product_name", "category_id"]
    ).drop_duplicates(subset=["product_id"])
    return df.reset_index(drop=True)


def clean_sales(df: pd.DataFrame) -> pd.DataFrame:
    df = normalize_columns(df)
    required = ["sale_id", "sale_date", "store_id", "product_id", "quantity"]
    for col in required:
        if col not in df.columns:
            raise KeyError(f"Missing required column in sales data: {col}")

    df["sale_id"] = df["sale_id"].astype(str).str.strip()   #type: ignore
    df["store_id"] = df["store_id"].astype(str).str.strip()   #type: ignore
    df["product_id"] = df["product_id"].astype(str).str.strip()   #type: ignore
    df["sale_date"] = pd.to_datetime(df["sale_date"], errors="coerce", dayfirst=True)   #type: ignore
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")   #type: ignore
    
    df = df[df["quantity"] > 0] #type: ignore
    
    df = df.dropna(
        subset=["sale_id", "sale_date", "store_id", "product_id"]
    ).drop_duplicates(subset=["sale_id"])
    
    return df.reset_index(drop=True)


def clean_stores(df: pd.DataFrame) -> pd.DataFrame:
    df = normalize_columns(df)
    required = ["store_id", "store_name", "city", "country"]
    for col in required:
        if col not in df.columns:
            raise KeyError(f"Missing required column in stores data: {col}")

    df["store_id"] = df["store_id"].astype(str).str.strip() #type: ignore
    df["store_name"] = df["store_name"].astype(str).str.strip() #type: ignore
    df["city"] = df["city"].astype(str).str.strip() #type: ignore
    df["country"] = df["country"].astype(str).str.strip()   #type: ignore
    
    df = df.dropna(
        subset=["store_id", "store_name", "city", "country"]
    ).drop_duplicates(subset=["store_id"])
    
    return df.reset_index(drop=True)


def clean_warranty(df: pd.DataFrame) -> pd.DataFrame:
    df = normalize_columns(df)
    required = ["claim_id", "claim_date", "sale_id", "repair_status"]
    for col in required:
        if col not in df.columns:
            raise KeyError(f"Missing required column in warranty data: {col}")

    df["claim_id"] = df["claim_id"].astype(str).str.strip()   #type: ignore
    df["sale_id"] = df["sale_id"].astype(str).str.strip()   #type: ignore
    df["claim_date"] = pd.to_datetime(df["claim_date"], errors="coerce")   #type: ignore
    df["repair_status"] = df["repair_status"].astype(str).str.strip().str.lower()   #type: ignore
    df = df.dropna(subset=["claim_id", "sale_id", "claim_date"]).drop_duplicates(
        subset=["claim_id"]
    )
    
    return df.reset_index(drop=True)


def clean_all_tables(raw_bundle: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    cleaned: dict[str, pd.DataFrame] = {}
    if "categories" in raw_bundle:
        cleaned["categories"] = clean_categories(raw_bundle["categories"])
    if "products" in raw_bundle:
        cleaned["products"] = clean_products(raw_bundle["products"])
    if "stores" in raw_bundle or "stores_json" in raw_bundle:
        source = raw_bundle.get("stores_json", raw_bundle.get("stores"))
        cleaned["stores"] = clean_stores(source)    #type: ignore
    if "sales" in raw_bundle:
        cleaned["sales"] = clean_sales(raw_bundle["sales"])
    if "warranty" in raw_bundle:
        cleaned["warranty"] = clean_warranty(raw_bundle["warranty"])
    return cleaned


def ensure_processed_dir(base_dir: str | None = None) -> str:
    base = Path(base_dir) if base_dir else Path(__file__).resolve().parents[1] / "data"
    processed = base / "processed"
    processed.mkdir(parents=True, exist_ok=True)
    return str(processed)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("Running data cleaning module as a script.")
    
    try:
        from src.extract import BaseDataLoader 
        
        extractor = BaseDataLoader()
        products = extractor.read_csv('src/data/raw/products.csv')
        sales = extractor.read_csv('src/data/raw/sales.csv')
        stores = extractor.read_csv('src/data/raw/stores.csv')
        warranty = extractor.read_csv('src/data/raw/warranty.csv')
        categories = extractor.read_csv('src/data/raw/category.csv')

        # Check duplicate rows
        logger.info("Duplicate rows")
        logger.info("Products:", products.duplicated().sum())
        logger.info("Sales:", sales.duplicated().sum())
        logger.info("Stores:", stores.duplicated().sum())
        logger.info("Warranty:", warranty.duplicated().sum())
        logger.info("Categories:", categories.duplicated().sum())

        logger.info("\n\nMissing values")
        logger.info("Products:", products.isnull().sum().to_dict())
        logger.info("Sales:", sales.isnull().sum().to_dict())
        logger.info("Stores:", stores.isnull().sum().to_dict())
        logger.info("Warranty:", warranty.isnull().sum().to_dict())
        logger.info("Categories:", categories.isnull().sum().to_dict())
        
        logger.info("\n\nData types")
        logger.info("Products:", products.dtypes.to_dict())
        logger.info("Sales:", sales.dtypes.to_dict())
        logger.info("Stores:", stores.dtypes.to_dict())
        logger.info("Warranty:", warranty.dtypes.to_dict())
        logger.info("Categories:", categories.dtypes.to_dict())

        logger.info("\n\nID uniqueness")
        logger.info("Product IDs:", products["Product_ID"].nunique(), "/", len(products))
        logger.info("Store IDs:", stores["Store_ID"].nunique(), "/", len(stores))
        logger.info("Sale IDs:", sales["sale_id"].nunique(), "/", len(sales))
        logger.info("Claim IDs:", warranty["claim_id"].nunique(), "/", len(warranty))
        logger.info("Category IDs:", categories["category_id"].nunique(), "/", len(categories))

        logger.info("\n\nForeign-key relationships")
        logger.info("Sales → Products:", sales["product_id"].isin(products["Product_ID"]).mean())
        logger.info("Sales → Stores:", sales["store_id"].isin(stores["Store_ID"]).mean())
        logger.info("Warranty → Sales:", warranty["sale_id"].isin(sales["sale_id"]).mean())

        logger.info("Product categories:")
        logger.info(products["Category_ID"].value_counts().sort_index())

        logger.info("\nCountries:")
        logger.info(stores["Country"].value_counts())

        logger.info("\nRepair statuses:")
        logger.info(warranty["repair_status"].value_counts())

        logger.info("\nQuantity:")
        logger.info(sales["quantity"].describe())

        # logger.info("\nSale date range:")
        # logger.info(sales["sale_date"].min(), "to", sales["sale_date"].max())

        # logger.info("\nLaunch date range:")
        # logger.info(products["Launch_Date"].min(), "to", products["Launch_Date"].max())

        logger.info("\nWarranty date range:")
        logger.info(warranty["claim_date"].min(), "to", warranty["claim_date"].max())


        logger.info("\n\nDuplicate primary-key values")

        logger.info("Products:", products["Product_ID"].duplicated().sum())
        logger.info("Stores:", stores["Store_ID"].duplicated().sum())
        logger.info("Sales:", sales["sale_id"].duplicated().sum())
        logger.info("Warranty:", warranty["claim_id"].duplicated().sum())
    
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        
    finally:
        logger.info("Data cleaning module execution completed.")