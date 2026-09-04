from datetime import datetime
import pytest
from sqlalchemy.exc import IntegrityError

from db.models import Product, Customer, Sale, Return
from db.repository import ProductRepository, CustomerRepository, SaleRepository, ReturnRepository   


def test_product_repository_crud(db_session):
    """Test full CRUD cycle for a model with a string Primary Key."""
    repo = ProductRepository(db_session)

    # 1. Create
    new_product = Product(stock_code="P100", description="Test Widget")
    created_product = repo.create(new_product)
    
    # 2. Read
    fetched_product = repo.get_by_id("P100")
    assert fetched_product is not None
    assert fetched_product.description == "Test Widget"
    
    # 3. Update
    updated_product = repo.update("P100", description="Updated Widget")
    assert updated_product.description == "Updated Widget"
    
    # 4. Delete
    delete_success = repo.delete("P100")
    assert delete_success is True
    assert repo.get_by_id("P100") is None


def test_customer_repository_crud(db_session):
    """Test full CRUD cycle for a model with an integer Primary Key."""
    repo = CustomerRepository(db_session)

    new_cust = Customer(customer_id=1001, country="United Kingdom")
    repo.create(new_cust)
    
    fetched = repo.get_by_id(1001)
    assert fetched.country == "United Kingdom"
    
    repo.update(1001, country="France")
    assert repo.get_by_id(1001).country == "France"


def test_sale_repository_with_valid_relations(db_session):
    """Test inserting a Fact record (Sale) ensuring foreign keys map correctly."""
    prod_repo = ProductRepository(db_session)
    cust_repo = CustomerRepository(db_session)
    sale_repo = SaleRepository(db_session)

    # Setup parent records
    prod_repo.create(Product(stock_code="P200", description="Gadget"))
    cust_repo.create(Customer(customer_id=2001, country="Germany"))

    # Create dependent Sale record
    sale = Sale(
        sale_id=1,
        invoice="INV-001",
        stock_code="P200",
        customer_id=2001,
        quantity=5,
        price=15.99,
        invoice_date=datetime(2026, 9, 3, 10, 0, 0)
    )
    created_sale = sale_repo.create(sale)
    
    assert created_sale.sale_id is not None
    assert created_sale.stock_code == "P200"

    # Verify cascading read
    fetched_sale = sale_repo.get_by_id(created_sale.sale_id)
    assert fetched_sale.quantity == 5


def test_sale_repository_foreign_key_violation(db_session):
    """Test that the repository handles and raises IntegrityErrors for FK violations."""
    sale_repo = SaleRepository(db_session)

    invalid_sale = Sale(
        invoice="INV-002",
        stock_code="MISSING_PROD",  # This product does not exist
        customer_id=9999,           # This customer does not exist
        quantity=2,
        price=10.00,
        invoice_date=datetime.now()
    )

    # The repo intercepts the DB error, rolls back the transaction, and re-raises it.
    with pytest.raises(IntegrityError):
        sale_repo.create(invalid_sale)


def test_get_all_pagination(db_session):
    """Test that get_all properly limits and offsets queries."""
    repo = CustomerRepository(db_session)
    
    # Insert 5 customers
    for i in range(1, 6):
        repo.create(Customer(customer_id=i, country="Country " + str(i)))
        
    results = repo.get_all(limit=2, offset=0)
    assert len(results) == 2
    assert results[0].customer_id == 1
    
    results_page_2 = repo.get_all(limit=2, offset=2)
    assert len(results_page_2) == 2
    assert results_page_2[0].customer_id == 3