# src/main.py
import logging
import sys
from pathlib import Path

# 1. Imports from your existing modules
from src.extract import main as extract_main
from src.transform import main as transform_main
from src.load import main as load_main

# Configure unified logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("ELT_Pipeline")


def run_pipeline():
    try:
        logger.info("Starting Extract step...")
        extract_main()

        logger.info("Starting Transform step...")
        transform_main()

        logger.info("Starting Load step...")
        load_main()

        logger.info("Pipeline executed successfully!")

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    run_pipeline()
