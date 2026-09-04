from pathlib import Path
from typing import Union
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent if "__file__" in locals() else Path.cwd()
RAW_DIR = BASE_DIR.parent / "data" / "raw"
PROCESSED_DIR = BASE_DIR.parent / "data" / "processed"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def read_csv(file_path: Union[str, Path], **kwargs) -> pd.DataFrame:
    """Reads a CSV file into a pandas DataFrame."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")
    return pd.read_csv(path, **kwargs)


def read_json(file_path: Union[str, Path], orient: str = "records", **kwargs) -> pd.DataFrame:
    """Reads a JSON file into a pandas DataFrame."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {path}")
    return pd.read_json(path, orient=orient, **kwargs)


def read_parquet(file_path: Union[str, Path], engine: str = "pyarrow", **kwargs) -> pd.DataFrame:
    """Reads a Parquet file into a pandas DataFrame."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Parquet file not found: {path}")
    return pd.read_parquet(path, engine=engine, **kwargs)


def write_parquet(
    df: pd.DataFrame,
    file_path: Union[str, Path],
    compression: str = "snappy",
    engine: str = "pyarrow",
) -> None:
    """Writes a DataFrame to a Parquet snapshot."""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, engine=engine, compression=compression, index=False)
    print(f"[EXTRACT] Snapshot saved -> {path} ({len(df):,} rows)")