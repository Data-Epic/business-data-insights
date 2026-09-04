from datetime import datetime
from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
)
from sqlalchemy.orm import DeclarativeBase



class Base(DeclarativeBase):
  pass

class Product(Base):
    __tablename__ = "products"

    stock_code = Column(String(50), primary_key=True)
    description = Column(String(255), nullable=True)


class Customer(Base):
    __tablename__ = "customers"

    customer_id = Column(BigInteger, primary_key=True, autoincrement=False)
    country = Column(String(100), nullable=False, default="Unknown")


class Sale(Base):
    __tablename__ = "sales"

    sale_id = Column(BigInteger, primary_key=True, autoincrement=True)
    invoice = Column(String(50), nullable=False, index=True)
    stock_code = Column(
        String(50),
        ForeignKey("products.stock_code", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    customer_id = Column(
        BigInteger,
        ForeignKey("customers.customer_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    quantity = Column(Numeric(12, 2), nullable=False)
    price = Column(Numeric(12, 4), nullable=False)
    invoice_date = Column(DateTime, nullable=False, index=True)

    __table_args__ = (
        CheckConstraint("quantity > 0", name="chk_sales_quantity_positive"),
        CheckConstraint("price >= 0", name="chk_sales_price_non_negative"),
        Index("idx_sales_cust_stock_date", "customer_id", "stock_code", "invoice_date"),
    )


class Return(Base):
    __tablename__ = "returns"

    return_id = Column(BigInteger, primary_key=True, autoincrement=True)
    sale_id = Column(
        BigInteger,
        ForeignKey("sales.sale_id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    invoice = Column(String(50), nullable=False)
    stock_code = Column(
        String(50),
        ForeignKey("products.stock_code", ondelete="RESTRICT"),
        nullable=False,
    )
    customer_id = Column(
        BigInteger,
        ForeignKey("customers.customer_id", ondelete="SET NULL"),
        nullable=True,
    )
    quantity = Column(Numeric(12, 2), nullable=False)
    price = Column(Numeric(12, 4), nullable=False)
    invoice_date = Column(DateTime, nullable=False)

    __table_args__ = (
        CheckConstraint("quantity > 0", name="chk_returns_quantity_positive"),
        CheckConstraint("price >= 0", name="chk_returns_price_non_negative"),
    )