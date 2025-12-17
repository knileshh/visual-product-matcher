"""
Database models and data structures for Visual Product Matcher.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import sqlite3
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class Product:
    """Product data structure."""
    id: int
    name: str
    image_path: str
    category: Optional[str] = None
    file_size: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    format: Optional[str] = None
    created_at: Optional[datetime] = None
    cloudinary_url: Optional[str] = None
    local_image_path: Optional[str] = None
    gcs_url: Optional[str] = None


class Database:
    """SQLite database manager for product metadata."""
    
    def __init__(self, db_path: str):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._ensure_database_exists()
        self._create_tables()
    
    def _ensure_database_exists(self) -> None:
        """Ensure database directory exists."""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
    
    def _create_tables(self) -> None:
        """Create database tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    image_path TEXT UNIQUE NOT NULL,
                    category TEXT,
                    file_size INTEGER,
                    width INTEGER,
                    height INTEGER,
                    format TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create index on image_path for faster lookups
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_image_path 
                ON products(image_path)
            """)
            
            conn.commit()
            logger.info("Database tables created successfully")
    
    def insert_product(self, product: Product) -> int:
        """
        Insert a new product into the database.
        
        Args:
            product: Product object to insert
            
        Returns:
            ID of inserted product
            
        Raises:
            sqlite3.IntegrityError: If product with same image_path exists
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO products 
                (name, image_path, category, file_size, width, height, format)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                product.name,
                product.image_path,
                product.category,
                product.file_size,
                product.width,
                product.height,
                product.format
            ))
            conn.commit()
            product_id = cursor.lastrowid
            logger.debug(f"Inserted product {product_id}: {product.name}")
            return product_id
    
    def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """
        Retrieve product by ID.
        
        Args:
            product_id: Product ID
            
        Returns:
            Product object or None if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM products WHERE id = ?
            """, (product_id,))
            row = cursor.fetchone()
            
            if row:
                return Product(**dict(row))
            return None
    
    def get_product_by_path(self, image_path: str) -> Optional[Product]:
        """
        Retrieve product by image path.
        
        Args:
            image_path: Path to product image
            
        Returns:
            Product object or None if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM products WHERE image_path = ?
            """, (image_path,))
            row = cursor.fetchone()
            
            if row:
                return Product(**dict(row))
            return None
    
    def get_all_products(self, limit: Optional[int] = None) -> list[Product]:
        """
        Retrieve all products from database.
        
        Args:
            limit: Maximum number of products to return
            
        Returns:
            List of Product objects
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if limit:
                cursor.execute("""
                    SELECT * FROM products LIMIT ?
                """, (limit,))
            else:
                cursor.execute("SELECT * FROM products")
            
            rows = cursor.fetchall()
            return [Product(**dict(row)) for row in rows]
    
    def get_product_count(self) -> int:
        """
        Get total number of products in database.
        
        Returns:
            Total product count
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM products")
            count = cursor.fetchone()[0]
            return count
    
    def delete_all_products(self) -> None:
        """Delete all products from database (use with caution)."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM products")
            conn.commit()
            logger.warning("All products deleted from database")
    
    def product_exists(self, image_path: str) -> bool:
        """
        Check if product with given image path exists.
        
        Args:
            image_path: Path to product image
            
        Returns:
            True if product exists, False otherwise
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM products WHERE image_path = ?
            """, (image_path,))
            count = cursor.fetchone()[0]
            return count > 0
