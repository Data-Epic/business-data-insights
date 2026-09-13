import pandas as pd
import pytest

from src.clean import clean_sales, clean_products, clean_stores, clean_warranty


@pytest.fixture
def raw_sales_sample():
    return pd.DataFrame({
        "sale_id": ["S1", "S2", "S2", "S3"],       # S2 duplicated on purpose
        "sale_date": ["05-07-2021", "20-07-2022", "20-07-2022", "not-a-date"],
        "store_id": ["ST-1", "ST-2", "ST-2", "ST-3"],
        "product_id": ["P-1", "P-2", "P-2", "P-3"],
        "quantity": [5, 9, 9, -1],                 # negative quantity should be dropped
    })


def test_clean_sales_drops_duplicate_sale_id(raw_sales_sample):
    result = clean_sales(raw_sales_sample)
    assert result["sale_id"].is_unique


def test_clean_sales_drops_invalid_quantity(raw_sales_sample):
    result = clean_sales(raw_sales_sample)
    assert (result["quantity"] > 0).all()


def test_clean_sales_parses_dates_to_datetime(raw_sales_sample):
    result = clean_sales(raw_sales_sample)
    assert pd.api.types.is_datetime64_any_dtype(result["sale_date"])


def test_clean_sales_drops_unparseable_dates(raw_sales_sample):
    result = clean_sales(raw_sales_sample)
    # the "not-a-date" row should be gone entirely
    assert "not-a-date" not in result["sale_date"].astype(str).values


@pytest.fixture
def raw_products_sample():
    return pd.DataFrame({
        "Product_ID": ["P-1", "P-1", "P-2"],       # P-1 duplicated on purpose
        "Product_Name": ["MacBook", "MacBook", "iPhone"],
        "Category_ID": ["CAT-1", "CAT-1", "CAT-2"],
        "Launch_Date": ["2023-09-17", "2023-09-17", "2022-09-16"],
        "Price": [1149, 1149, -50],                # negative price should be dropped
    })


def test_clean_products_drops_duplicate_product_id(raw_products_sample):
    result = clean_products(raw_products_sample)
    assert result["Product_ID"].is_unique


def test_clean_products_drops_invalid_price(raw_products_sample):
    result = clean_products(raw_products_sample)
    assert (result["Price"] > 0).all()


def test_clean_products_category_is_category_dtype(raw_products_sample):
    result = clean_products(raw_products_sample)
    assert str(result["Category_ID"].dtype) == "category"