# tests/test_repository.py
import pytest
import psycopg2

from src.db import get_connection


def test_sale_with_invalid_product_id_fails():
    conn = get_connection()
    cur = conn.cursor()
    with pytest.raises(psycopg2.errors.ForeignKeyViolation):
        cur.execute(
            """INSERT INTO sales (sale_id, sale_date, store_id, product_id, quantity)
               VALUES ('TEST-BAD', '2024-01-01', 'ST-1', 'DOES-NOT-EXIST', 1);"""
        )
        conn.commit()
    conn.rollback()
    cur.close()
    conn.close()


def test_sale_with_zero_quantity_fails():
    """quantity must be > 0 per the CHECK constraint."""
    conn = get_connection()
    cur = conn.cursor()
    with pytest.raises(psycopg2.errors.CheckViolation):
        cur.execute(
            """INSERT INTO sales (sale_id, sale_date, store_id, product_id, quantity)
               VALUES ('TEST-BAD2', '2024-01-01', 'ST-1', 'P-1', 0);"""
        )
        conn.commit()
    conn.rollback()
    cur.close()
    conn.close()

