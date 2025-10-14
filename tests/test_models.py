"""
Tests for Database models.
"""
import pytest
from src.models import Product


def test_database_initialization(temp_db):
    """Test database initialization."""
    assert temp_db is not None
    assert temp_db.get_product_count() == 0


def test_insert_product(temp_db, sample_product):
    """Test inserting a product."""
    product_id = temp_db.insert_product(sample_product)
    
    assert product_id > 0
    assert temp_db.get_product_count() == 1


def test_get_product_by_id(temp_db, sample_product):
    """Test retrieving product by ID."""
    product_id = temp_db.insert_product(sample_product)
    
    retrieved = temp_db.get_product_by_id(product_id)
    
    assert retrieved is not None
    assert retrieved.name == sample_product.name
    assert retrieved.image_path == sample_product.image_path


def test_get_product_by_path(temp_db, sample_product):
    """Test retrieving product by image path."""
    temp_db.insert_product(sample_product)
    
    retrieved = temp_db.get_product_by_path(sample_product.image_path)
    
    assert retrieved is not None
    assert retrieved.name == sample_product.name


def test_get_all_products(temp_db, sample_product):
    """Test retrieving all products."""
    # Insert multiple products
    for i in range(5):
        product = Product(
            id=0,
            name=f'Product {i}',
            image_path=f'/path/to/image{i}.jpg',
            category='Fashion'
        )
        temp_db.insert_product(product)
    
    products = temp_db.get_all_products()
    
    assert len(products) == 5


def test_get_all_products_with_limit(temp_db, sample_product):
    """Test retrieving products with limit."""
    # Insert multiple products
    for i in range(10):
        product = Product(
            id=0,
            name=f'Product {i}',
            image_path=f'/path/to/image{i}.jpg',
            category='Fashion'
        )
        temp_db.insert_product(product)
    
    products = temp_db.get_all_products(limit=3)
    
    assert len(products) == 3


def test_product_exists(temp_db, sample_product):
    """Test checking if product exists."""
    assert temp_db.product_exists(sample_product.image_path) is False
    
    temp_db.insert_product(sample_product)
    
    assert temp_db.product_exists(sample_product.image_path) is True


def test_duplicate_product_insert(temp_db, sample_product):
    """Test inserting duplicate product (same image path)."""
    temp_db.insert_product(sample_product)
    
    # Attempting to insert duplicate should raise error
    with pytest.raises(Exception):  # SQLite IntegrityError
        temp_db.insert_product(sample_product)


def test_get_nonexistent_product(temp_db):
    """Test retrieving non-existent product."""
    retrieved = temp_db.get_product_by_id(999)
    
    assert retrieved is None


def test_delete_all_products(temp_db, sample_product):
    """Test deleting all products."""
    temp_db.insert_product(sample_product)
    assert temp_db.get_product_count() == 1
    
    temp_db.delete_all_products()
    
    assert temp_db.get_product_count() == 0
