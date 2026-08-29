from __future__ import annotations

import logging
from pathlib import Path
import pandas as pd

from src.clean import clean_all_tables
from src.extract import BaseDataLoader, export_stores_json, load_dataset_bundle

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(filename)s:%(funcName)s:%(lineno)d - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
    
def run_transform_pipeline(
    data_dir: str | Path | None = None,
) -> dict[str, pd.DataFrame]:
    
    root = Path(data_dir) if data_dir else DATA_DIR
    raw_dir = root / "raw"
    processed_dir = root / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    raw_bundle = load_dataset_bundle(raw_dir)
    if "stores" in raw_bundle and not (raw_dir / "stores.json").exists():
        export_stores_json(raw_dir / "stores.csv", raw_dir / "stores.json")

    cleaned = clean_all_tables(raw_bundle)
    for name, frame in cleaned.items():
        output_path = processed_dir / f"{name}.parquet"
        BaseDataLoader.save_parquet(frame, output_path)

    sales_clean = cleaned.get("sales")
    if sales_clean is not None and "product_id" in sales_clean.columns:
        enriched = sales_clean.merge(
            cleaned["products"][["product_id", "price", "category_id"]],
            on="product_id",
            how="left",
        )
        enriched["revenue"] = (enriched["quantity"] * enriched["price"]).fillna(0)
        enriched["month"] = enriched["sale_date"].dt.to_period("M").astype(str)
        BaseDataLoader.save_parquet(enriched, processed_dir / "sales_enriched.parquet")

    return cleaned


def main():
    run_transform_pipeline()
    
    
if __name__ == "__main__":
    main()
