from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import List, Optional

from src.clean import clean_all_tables
from src.db import apply_schema, get_connection
from src.extract import load_dataset_bundle
from src.repository import SalesRepository

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(filename)s:%(funcName)s:%(lineno)d - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

all_tables = ["categories", "products", "stores", "sales", "warranty"]


def run_load_pipeline(
    tables_to_load: Optional[List[str]] = None,
    resume: bool = True,
    batch_size: int = 50_000,
    data_dir: str | Path | None = None,
) -> None:
    """Orchestrates data pipeline extraction, cleaning, and batched persistence."""
    tables = tables_to_load or all_tables
    base_dir = (
        Path(data_dir) if data_dir else Path(__file__).resolve().parents[1] / "data"
    )
    raw_dir = base_dir / "raw"

    logger.info(f"Extracting datasets from {raw_dir}...")
    raw_bundle = load_dataset_bundle(raw_dir)

    logger.info("Cleaning raw data tables...")
    cleaned = clean_all_tables(raw_bundle)

    conn = get_connection()
    repo = SalesRepository(conn, batch_size=batch_size)

    try:
        schema_path = Path(__file__).resolve().parents[1] / "db" / "schema.sql"
        apply_schema(conn, schema_path)

        for table in tables:
            if table not in cleaned:
                logger.warning(
                    f"Table '{table}' not found in cleaned dataset. Skipping."
                )
                continue

            logger.info(f"Processing table: {table} (Resume={resume})")

            # Map table names to repository calls or direct batch_loader execution
            if table == "categories":
                repo.insert_categories(cleaned["categories"], resume=resume)
            elif table == "products":
                repo.insert_products(cleaned["products"], resume=resume)
            elif table == "stores":
                repo.insert_stores(cleaned["stores"], resume=resume)
            elif table == "sales":
                repo.insert_sales(cleaned["sales"], resume=resume)
            elif table == "warranty":
                repo.insert_warranty(cleaned["warranty"], resume=resume)

        logger.info("Pipeline load operation completed.")

    except Exception:
        conn.rollback()
        logger.exception("Pipeline loading failed")
        raise
    finally:
        repo.close()
        conn.close()


def parse_args():
    parser = argparse.ArgumentParser(description="CLI Data Loader for Sales Pipeline")
    parser.add_argument(
        "--tables",
        nargs="+",
        choices=all_tables,
        default=all_tables,
        help="Specify which tables to load into PostgreSQL (e.g., --tables sales warranty).",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        default=True,
        help="Resume loading from the last committed row index checkpoint (default: True).",
    )
    parser.add_argument(
        "--no-resume",
        dest="resume",
        action="store_false",
        help="Start ingestion from row index 0, ignoring previous checkpoints.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50_000,
        help="Number of rows per commit batch (default: 50,000).",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    run_load_pipeline(
        tables_to_load=args.tables,
        resume=args.resume,
        batch_size=args.batch_size,
    )   


if __name__ == "__main__":
    main()
