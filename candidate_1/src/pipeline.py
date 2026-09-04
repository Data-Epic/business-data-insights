import sys
import time
from loggings.logging import logger
from pathlib import Path
from alembic.config import Config
from alembic import command

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Import your pipeline modules
from .clean import run_cleaning_pipeline
from db.load import load_parquet_to_dw
from .aggregate import run_aggregations



def apply_migrations():
    """Programmatically executes 'alembic upgrade head'."""
    logger.info("Checking database schema and applying migrations...")
    try:
        # Load the alembic.ini configuration file from the project root
        alembic_cfg = Config(str(BASE_DIR / "alembic.ini"))
        command.upgrade(alembic_cfg, "head")
        logger.info("Database schema is up to date.")
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise


def run_pipeline():
    """Executes the full Extract, Transform, Load, and Reporting pipeline."""
    start_time = time.perf_counter()
    logger.info("=== Starting Retail ETL Pipeline ===")

    try:
        logger.info("--- PHASE 1: Extract & Clean ---")
        run_cleaning_pipeline()

        logger.info("--- PHASE 2: Schema Migration ---")
        apply_migrations()

        logger.info("--- PHASE 3: Data Warehouse Load ---")
        load_parquet_to_dw()

        logger.info("--- PHASE 4: Business Aggregations & Reporting ---")
        run_aggregations()

        elapsed_time = time.perf_counter() - start_time
        logger.info(f"=== Pipeline completed successfully in {elapsed_time:.2f} seconds ===")

    except Exception as e:
        logger.error("Pipeline terminated due to an error.", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    run_pipeline()