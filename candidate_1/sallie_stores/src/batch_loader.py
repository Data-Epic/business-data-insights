import logging
from pathlib import Path
from typing import Dict, List, Generator, Optional

import pandas as pd

from src.extract import BaseDataLoader

logger = logging.getLogger(__name__)


class BatchLoader:
    """
    Loads DataFrames into PostgreSQL in batches.

    Each batch is committed independently.
    A persistent checkpoint records the last successfully
    committed row, allowing interrupted loads to resume.
    """

    def __init__(
        self,
        conn,
        data_loader: Optional[BaseDataLoader] = None,
        batch_size: int = 50_000,
        table_columns: Optional[Dict[str, List[str]]] = None,
    ):
        self.conn = conn
        self.cur = conn.cursor()
        self.loader = data_loader or BaseDataLoader()
        self.batch_size = batch_size
        self.table_columns = table_columns or {}

        self.cache: Dict[str, pd.DataFrame] = {}

        self._ensure_checkpoint_table()

    def _ensure_checkpoint_table(self) -> None:
        """Create the checkpoint table if it does not already exist."""

        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS _ingestion_checkpoints (
                table_name VARCHAR(100) PRIMARY KEY,
                last_processed_row_index BIGINT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)

        self.conn.commit()

    def get_checkpoint(self, table_name: str) -> int:
        """Return the next row index to process for a table."""

        self.cur.execute(
            """
            SELECT last_processed_row_index
            FROM _ingestion_checkpoints
            WHERE table_name = %s;
            """,
            (table_name,),
        )

        row = self.cur.fetchone()

        return row[0] if row else 0

    def update_checkpoint(
        self,
        table_name: str,
        row_index: int,
    ) -> None:
        """Update the checkpoint inside the current transaction."""

        self.cur.execute(
            """
            INSERT INTO _ingestion_checkpoints (
                table_name,
                last_processed_row_index,
                updated_at
            )
            VALUES (%s, %s, CURRENT_TIMESTAMP)

            ON CONFLICT (table_name)
            DO UPDATE SET
                last_processed_row_index = EXCLUDED.last_processed_row_index,
                updated_at = CURRENT_TIMESTAMP;
            """,
            (table_name, row_index),
        )

    def get_or_load_dataframe(
        self,
        data_path: Path,
        table_name: str,
    ) -> pd.DataFrame:
        """Load a DataFrame using the appropriate extractor."""

        if table_name not in self.cache:

            logger.info(
                "Loading '%s' from %s",
                table_name,
                data_path,
            )

            if data_path.suffix == ".parquet":
                df = self.loader.read_parquet(data_path)

            elif data_path.suffix == ".csv":
                df = self.loader.read_csv(data_path)

            elif data_path.suffix == ".json":
                df = self.loader.read_json(data_path)

            else:
                raise ValueError(f"Unsupported file format: {data_path.suffix}")

            self.cache[table_name] = df

        else:
            logger.info(
                "Using cached DataFrame for '%s'",
                table_name,
            )

        return self.cache[table_name]

    def clear_cache(
        self,
        table_name: Optional[str] = None,
    ) -> None:
        """Clear one table or the entire DataFrame cache."""

        if table_name:

            if table_name in self.cache:
                del self.cache[table_name]

                logger.info(
                    "Cleared cache for table '%s'",
                    table_name,
                )

        else:

            self.cache.clear()

            logger.info("Cleared entire DataFrame cache")

    def batch_generator(
        self,
        df: pd.DataFrame,
        start_row: int = 0,
    ) -> Generator[tuple[int, pd.DataFrame], None, None]:
        """Yield batches beginning at start_row."""

        total_rows = len(df)

        total_batches = (total_rows + self.batch_size - 1) // self.batch_size

        start_batch = start_row // self.batch_size

        for batch_idx in range(
            start_batch,
            total_batches,
        ):

            start = batch_idx * self.batch_size

            end = min(
                start + self.batch_size,
                total_rows,
            )

            yield batch_idx, df.iloc[start:end] #type: ignore

    def load_table(
        self,
        table_name: str,
        data_or_path: Path | pd.DataFrame,
        resume: bool = True,
        conflict_target: Optional[str] = None,
        clear_cache_after: bool = False,
    ) -> None:
        """Load a table in batches with persistent checkpoints."""

        if isinstance(data_or_path, Path):
            df = self.get_or_load_dataframe(
            data_or_path,
            table_name,
            )
        elif isinstance(data_or_path, pd.DataFrame):
            df = data_or_path

        if df.empty:
            logger.warning(
                "DataFrame for '%s' is empty. Skipping.",
                table_name,
            )
            return


        if self.table_columns and table_name in self.table_columns:
            expected_columns = self.table_columns[table_name]

            df = df[expected_columns]

        else:
            expected_columns = df.columns.tolist()

        columns = ", ".join(expected_columns)

        placeholders = ", ".join(["%s"] * len(expected_columns))

        if conflict_target:

            sql = f"""
                INSERT INTO {table_name}
                ({columns})
                VALUES ({placeholders})
                ON CONFLICT ({conflict_target})
                DO NOTHING;
            """

        else:

            sql = f"""
                INSERT INTO {table_name}
                ({columns})
                VALUES ({placeholders})
                ON CONFLICT DO NOTHING;
            """

        total_rows = len(df)

        # Determine where to resume loading.
        start_row = self.get_checkpoint(table_name) if resume else 0

        if start_row >= total_rows:

            logger.info(
                "[%s] Already complete: %s/%s rows",
                table_name,
                total_rows,
                total_rows,
            )

            return

        logger.info(
            "[%s] Starting load: %s rows | batch size: %s | " "starting row: %s",
            table_name,
            total_rows,
            self.batch_size,
            start_row,
        )

        try:

            for batch_idx, batch in self.batch_generator(
                df, #type: ignore
                start_row=start_row,
            ):

                batch_start = batch_idx * self.batch_size
                batch_end = batch_start + len(batch)

                batch_data = [
                    tuple(row)
                    for row in batch.itertuples(
                        index=False,
                        name=None,
                    )
                ]

                self.cur.executemany(
                    sql,
                    batch_data,
                )

                self.update_checkpoint(
                    table_name,
                    batch_end,
                )

                # Commit insert and checkpoint together.
                self.conn.commit()

                progress = (batch_end / total_rows) * 100

                logger.info(
                    "[%s] Batch %s committed | " "rows %s-%s / %s | %.1f%%",
                    table_name,
                    batch_idx + 1,
                    batch_start,
                    batch_end,
                    total_rows,
                    progress,
                )

        except Exception:

            self.conn.rollback()

            logger.exception(
                "[%s] Load failed. " "Checkpoint remains at row %s.",
                table_name,
                self.get_checkpoint(table_name),
            )

            raise

        finally:

            if clear_cache_after:
                self.clear_cache(table_name)

    def close(self) -> None:
        """Close the cursor and clear cached DataFrames."""

        self.clear_cache()

        self.cur.close()
