from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import pandas as pd

from src.batch_loader import BatchLoader

logger = logging.getLogger(__name__)


class SalesRepository:
    """PostgreSQL Repository layer for executing business queries and batched data loading."""

    def __init__(self, conn, batch_size: int = 50_000):
        self.conn = conn
        self.cursor = conn.cursor()
        self.batch_loader = BatchLoader(conn=self.conn, batch_size=batch_size)

    def insert_categories(
        self,
        data_path_or_df: Path | pd.DataFrame,
        resume: bool = True,
        clear_cache: bool = True,
    ) -> None:
        self._load_table(
            "categories",
            data_path_or_df,
            conflict_target="category_id",
            resume=resume,
            clear_cache=clear_cache,
        )

    def insert_products(
        self,
        data_path_or_df: Path | pd.DataFrame,
        resume: bool = True,
        clear_cache: bool = True,
    ) -> None:
        self._load_table(
            "products",
            data_path_or_df,
            conflict_target="product_id",
            resume=resume,
            clear_cache=clear_cache,
        )

    def insert_stores(
        self,
        data_path_or_df: Path | pd.DataFrame,
        resume: bool = True,
        clear_cache: bool = True,
    ) -> None:
        self._load_table(
            "stores",
            data_path_or_df,
            conflict_target="store_id",
            resume=resume,
            clear_cache=clear_cache,
        )

    def insert_sales(
        self,
        data_path_or_df: Path | pd.DataFrame,
        resume: bool = True,
        clear_cache: bool = True,
    ) -> None:
        self._load_table(
            "sales",
            data_path_or_df,
            conflict_target="sale_id",
            resume=resume,
            clear_cache=clear_cache,
        )

    def insert_warranty(
        self,
        data_path_or_df: Path | pd.DataFrame,
        resume: bool = True,
        clear_cache: bool = True,
    ) -> None:
        self._load_table(
            "warranty",
            data_path_or_df,
            conflict_target="claim_id",
            resume=resume,
            clear_cache=clear_cache,
        )

    def _load_table(
        self,
        table_name: str,
        data: Path | pd.DataFrame,
        conflict_target: str,
        resume: bool = True,
        clear_cache: bool = True,
    ) -> None:
        
        """Internal helper to dispatch data loading through BatchLoader."""
        if isinstance(data, Path):
            self.batch_loader.load_table(
                table_name=table_name,
                data_or_path=data,
                resume=resume,
                conflict_target=conflict_target,
                clear_cache_after=clear_cache,
            )
        elif isinstance(data, pd.DataFrame):
            if data.empty:
                logger.info(f"Skipping load for empty DataFrame: {table_name}")
                return

            # Seed batch loader cache directly when receiving an in-memory DataFrame
            self.batch_loader.cache[table_name] = data
            self.batch_loader.load_table(
                table_name=table_name,
                data_or_path=data,
                resume=resume,
                conflict_target=conflict_target,
                clear_cache_after=clear_cache,
            )

    def fetch_top_products_per_store(self, top_n: int = 3) -> pd.DataFrame:
        query = """
            WITH store_product_sales AS (
                SELECT
                    s.store_id,
                    st.store_name,
                    p.product_id,
                    p.product_name,
                    SUM(s.quantity * p.price) AS total_revenue,
                    ROW_NUMBER() OVER (
                        PARTITION BY s.store_id
                        ORDER BY SUM(s.quantity * p.price) DESC, p.product_id
                    ) AS revenue_rank
                FROM sales s
                JOIN products p ON s.product_id = p.product_id
                JOIN stores st ON s.store_id = st.store_id
                GROUP BY s.store_id, st.store_name, p.product_id, p.product_name
            )
            SELECT store_id, store_name, product_id, product_name, total_revenue, revenue_rank
            FROM store_product_sales
            WHERE revenue_rank <= %s
            ORDER BY store_id, revenue_rank
        """
        self.cursor.execute(query, (top_n,))
        rows = self.cursor.fetchall()
        columns = [col[0] for col in self.cursor.description]
        return pd.DataFrame(rows, columns=columns)

    def fetch_warranty_claim_rate_by_category(self) -> pd.DataFrame:
        query = """
            WITH sales_by_category AS (
                SELECT p.category_id, COUNT(s.sale_id) AS total_sales
                FROM sales s
                JOIN products p ON s.product_id = p.product_id
                GROUP BY p.category_id
            ),
            claims_by_category AS (
                SELECT p.category_id, COUNT(w.claim_id) AS total_claims
                FROM warranty w
                JOIN sales s ON w.sale_id = s.sale_id
                JOIN products p ON s.product_id = p.product_id
                GROUP BY p.category_id
            )
            SELECT
                sc.category_id,
                sc.total_sales,
                COALESCE(cc.total_claims, 0) AS total_claims,
                ROUND((COALESCE(cc.total_claims, 0)::numeric / sc.total_sales::numeric) * 100, 2) AS claim_rate_pct
            FROM sales_by_category sc
            LEFT JOIN claims_by_category cc ON sc.category_id = cc.category_id
            ORDER BY claim_rate_pct DESC
        """
        self.cursor.execute(query)
        rows = self.cursor.fetchall()
        columns = [col[0] for col in self.cursor.description]
        return pd.DataFrame(rows, columns=columns)

    def fetch_revenue_by_month(self) -> pd.DataFrame:
        query = """
            SELECT
                TO_CHAR(s.sale_date, 'YYYY-MM') AS month,
                SUM(s.quantity * p.price) AS revenue
            FROM sales s
            JOIN products p ON s.product_id = p.product_id
            GROUP BY TO_CHAR(s.sale_date, 'YYYY-MM')
            ORDER BY month
        """
        self.cursor.execute(query)
        rows = self.cursor.fetchall()
        columns = [col[0] for col in self.cursor.description]
        return pd.DataFrame(rows, columns=columns)

    def close(self) -> None:
        self.batch_loader.close()
        self.cursor.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("SalesRepository initialized successfully.")
