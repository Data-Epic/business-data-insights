from typing import Any
import pandas as pd
from sqlalchemy import text
from .db_config import get_connection

from typing import TypeVar, Generic, Type, Optional, Sequence
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete
from sqlalchemy.exc import SQLAlchemyError

# Assuming you have a Base declarative model
from .models import Base, Product, Customer, Sale, Return
from loggings.logging import logger

# Define a type variable that binds to your SQLAlchemy declarative base
ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    """Generic base repository providing full CRUD operations for any SQLAlchemy model."""

    def __init__(self, model_cls: type[ModelType], session: Session):
        self.model_cls = model_cls
        self.session = session
        self.model_name = model_cls.__name__


    def create(self, instance: ModelType) -> ModelType:
        """Persists a new model record."""
        try:
            logger.info(f"Creating {self.model_name}: {instance}")
            self.session.add(instance)
            self.session.commit()
            self.session.refresh(instance)
            logger.info(f"Successfully created {self.model_name}")
            return instance
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error creating {self.model_name}: {e}", exc_info=True)
            raise e


    def get_by_id(self, record_id: int | str) -> ModelType | None:
        """Retrieves a single record by its primary key ID."""
        try:
            logger.info(f"Retrieving {self.model_name} by ID: {record_id}")
            record = self.session.get(self.model_cls, record_id)
            if record:
                logger.info(f"Found {self.model_name}: {record}")
            else:
                logger.warning(
                    f"{self.model_name} with ID {record_id} does not exist."
                )
            return record
        except Exception as e:
            logger.error(
                f"Error fetching {self.model_name} with ID {record_id}: {e}",
                exc_info=True,
            )
            raise e


    def get_all(self, limit: int = 100, offset: int = 0) -> Sequence[ModelType]:
        """Retrieves all records with pagination."""
        try:
            stmt = select(self.model_cls).offset(offset).limit(limit)
            return self.session.scalars(stmt).all()
        except Exception as e:
            logger.error(f"Error fetching {self.model_name} records: {e}")
            raise e


    def update(self, record_id: int | str, **kwargs: Any) -> ModelType | None:
        """Dynamically updates attributes of an existing record."""
        try:
            record = self.get_by_id(record_id)
            if not record:
                return None

            valid_columns = set(self.model_cls.__table__.columns.keys())
            for field, value in kwargs.items():
                if field in valid_columns and value is not None:
                    setattr(record, field, value)

            self.session.commit()
            self.session.refresh(record)
            logger.info(f"Updated {self.model_name} with ID {record_id}")
            return record
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error updating {self.model_name} ID {record_id}: {e}")
            raise e


    def delete(self, record_id: int | str) -> bool:
        """Deletes a record by ID."""
        try:
            record = self.get_by_id(record_id)
            if not record:
                return False

            self.session.delete(record)
            self.session.commit()
            logger.info(f"Deleted {self.model_name} with ID {record_id}")
            return True
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error deleting {self.model_name} ID {record_id}: {e}")
            raise e



class ProductRepository(BaseRepository[Product]):
    """Repository for managing Product records in the database."""

    def __init__(self, session: Session):
        super().__init__(model_cls=Product, session=session)


class CustomerRepository(BaseRepository[Customer]):
    """Repository for managing Customer records in the database."""
    def __init__(self, session: Session):
        super().__init__(model_cls=Customer, session=session)

                    
class SaleRepository(BaseRepository[Sale]):
    """Repository for managing Sale records in the database."""

    def __init__(self, session: Session):
        super().__init__(model_cls=Sale, session=session)

class ReturnRepository(BaseRepository[Return]):
    """Repository for managing Return records in the database."""

    def __init__(self, session: Session):
        super().__init__(model_cls=Return, session=session)



class RetailRepository:

    @staticmethod
    def get_top_products_per_country(top_rank: int = 3) -> pd.DataFrame:
        """Query 1: Window function (DENSE_RANK) ranking top products by revenue per country."""
        sql = text("""
            WITH product_country_sales AS (
                SELECT
                    c.country,
                    p.stock_code,
                    p.description,
                    SUM(s.quantity * s.price) AS total_revenue,
                    DENSE_RANK() OVER (
                        PARTITION BY c.country 
                        ORDER BY SUM(s.quantity * s.price) DESC
                    ) as rank
                FROM sales s
                JOIN customers c ON s.customer_id = c.customer_id
                JOIN products p ON s.stock_code = p.stock_code
                GROUP BY c.country, p.stock_code, p.description
            )
            SELECT 
                country,
                rank,
                stock_code,
                description,
                ROUND(total_revenue, 2) AS total_revenue
            FROM product_country_sales
            WHERE rank <= :top_rank
            ORDER BY country ASC, rank ASC;
        """)

        with get_connection() as conn:
            result = conn.execute(sql, {"top_rank": top_rank})
            return pd.DataFrame(result.fetchall(), columns=result.keys())

    @staticmethod
    def get_product_return_rates(min_sales_volume: int = 100) -> pd.DataFrame:
        """Query 2: CTE joining sales and returns to calculate return rate % per product."""
        sql = text("""
            WITH sales_agg AS (
                SELECT 
                    stock_code,
                    SUM(quantity) AS total_sold_qty,
                    SUM(quantity * price) AS total_sold_rev
                FROM sales
                GROUP BY stock_code
            ),
            returns_agg AS (
                SELECT 
                    stock_code,
                    SUM(quantity) AS total_returned_qty
                FROM returns
                GROUP BY stock_code
            )
            SELECT 
                p.stock_code,
                p.description,
                s.total_sold_qty,
                COALESCE(r.total_returned_qty, 0) AS total_returned_qty,
                ROUND(
                    (COALESCE(r.total_returned_qty, 0)::numeric / s.total_sold_qty::numeric) * 100, 
                    2
                ) AS return_rate_pct
            FROM sales_agg s
            JOIN products p ON s.stock_code = p.stock_code
            LEFT JOIN returns_agg r ON s.stock_code = r.stock_code
            WHERE s.total_sold_qty >= :min_sales_volume
            ORDER BY return_rate_pct DESC
            LIMIT 10;
        """)

        with get_connection() as conn:
            result = conn.execute(sql, {"min_sales_volume": min_sales_volume})
            return pd.DataFrame(result.fetchall(), columns=result.keys())


if __name__ == "__main__":
    repo = RetailRepository()
    print("--- Top 3 Products Per Country (Sample) ---")
    print(repo.get_top_products_per_country(top_rank=3).head(15).to_string(index=False))

    print("\n--- Product Return Rates (Top 10) ---")
    print(repo.get_product_return_rates(min_sales_volume=100).to_string(index=False))