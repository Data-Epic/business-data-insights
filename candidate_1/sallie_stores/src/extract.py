from __future__ import annotations
from pathlib import Path
from typing import Any, Union

import pandas as pd
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(filename)s:%(funcName)s:%(lineno)d - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)



class BaseDataLoader:
    """Small reusable reader/writer layer for CSV, JSON, and Parquet sources."""

    @staticmethod
    def read_csv(filepath: Union[str, Path], **kwargs) -> pd.DataFrame:
        path = Path(filepath)
        if not path.is_file():
            raise FileNotFoundError(f"File not found: {path}")
        return pd.read_csv(path, **kwargs)

    @staticmethod
    def read_json(filepath: Union[str, Path], **kwargs) -> pd.DataFrame:
        path = Path(filepath)
        if not path.is_file():
            raise FileNotFoundError(f"File not found: {path}")
        return pd.read_json(path, **kwargs)

    @staticmethod
    def read_parquet(filepath: Union[str, Path], **kwargs) -> pd.DataFrame:
        path = Path(filepath)
        if not path.is_file():
            raise FileNotFoundError(f"File not found: {path}")
        return pd.read_parquet(path, engine="pyarrow", **kwargs)

    @staticmethod
    def save_parquet(df: pd.DataFrame, output_path: Union[str, Path]) -> Path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(path, engine="pyarrow", index=False)
        return path

    @staticmethod
    def write_json(
        df: pd.DataFrame, output_path: Union[str, Path], orient: str = "records"
    ) -> Path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_json(path, orient=orient, indent=4)   #type: ignore
        return path

    @staticmethod
    def convert_csv_to_json(
        csv_path: Union[str, Path], json_path: Union[str, Path]
    ) -> Path:
        c_path, j_path = Path(csv_path), Path(json_path)
        df = BaseDataLoader.read_csv(c_path)
        return BaseDataLoader.write_json(df, j_path)


def load_dataset_bundle(data_dir: Union[str, Path]) -> dict[str, pd.DataFrame]:
    base = Path(data_dir)
    raw_dir = base / "raw" if base.name != "raw" else base
    bundle: dict[str, pd.DataFrame] = {}
    aliases = {
        "category.csv": "categories",
        "categories.csv": "categories",
        "products.csv": "products",
        "sales.csv": "sales",
        "stores.csv": "stores",
        "warranty.csv": "warranty",
    }
    for file_name, alias in aliases.items():
        path = raw_dir / file_name
        if path.exists():
            bundle[alias] = BaseDataLoader.read_csv(path)
    stores_json_path = raw_dir / "stores.json"
    if stores_json_path.exists():
        bundle["stores_json"] = BaseDataLoader.read_json(stores_json_path)
    return bundle


def export_stores_json(
    raw_stores_csv: Union[str, Path], output_json: Union[str, Path]
) -> Path:
    df = BaseDataLoader.read_csv(raw_stores_csv)
    return BaseDataLoader.write_json(df, output_json)

def main():
    """
    Main extraction orchestrator:
    1. Ensures required raw conversion (CSV -> JSON for stores) takes place.
    2. Loads and returns all raw tables as a dictionary bundle.
    """

    project_root = Path(__file__).resolve().parents[1]
    raw_dir = project_root / "data" / "raw"

    bundle = load_dataset_bundle(raw_dir)

    if "stores" in bundle and not (raw_dir / "stores.json").exists():
        export_stores_json(raw_dir / "stores.csv", raw_dir / "stores.json")

    logger.info(f"Loaded raw dataset bundle with {len(bundle)} tables.")
    logger.info(sorted(bundle.keys()))

if __name__ == "__main__":
    main()
