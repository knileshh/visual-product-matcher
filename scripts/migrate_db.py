"""
Add cloudinary_url column to products table.
Migration script to update existing database schema.
"""
import sqlite3
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_database(db_path: str = "data/products.db"):
    """
    Add cloudinary_url and local_image_path columns to products table.
    
    Args:
        db_path: Path to SQLite database file
    """
    if not Path(db_path).exists():
        logger.error(f"Database not found: {db_path}")
        return False
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Check if columns already exist
            cursor.execute("PRAGMA table_info(products)")
            columns = [row[1] for row in cursor.fetchall()]
            
            # Add cloudinary_url column if it doesn't exist
            if 'cloudinary_url' not in columns:
                logger.info("Adding cloudinary_url column...")
                cursor.execute("""
                    ALTER TABLE products 
                    ADD COLUMN cloudinary_url TEXT
                """)
                logger.info("✓ Added cloudinary_url column")
            else:
                logger.info("cloudinary_url column already exists")
            
            # Add local_image_path column if it doesn't exist
            if 'local_image_path' not in columns:
                logger.info("Adding local_image_path column...")
                cursor.execute("""
                    ALTER TABLE products 
                    ADD COLUMN local_image_path TEXT
                """)
                logger.info("✓ Added local_image_path column")
            else:
                logger.info("local_image_path column already exists")
            
            # Create index on cloudinary_url for faster lookups
            try:
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_cloudinary_url 
                    ON products(cloudinary_url)
                """)
                logger.info("✓ Created index on cloudinary_url")
            except sqlite3.OperationalError:
                pass  # Index might already exist
            
            conn.commit()
            
            # Show table structure
            cursor.execute("PRAGMA table_info(products)")
            columns_info = cursor.fetchall()
            
            logger.info("\nCurrent table structure:")
            for col in columns_info:
                logger.info(f"  {col[1]} ({col[2]})")
            
            return True
    
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate database schema")
    parser.add_argument(
        '--db-path',
        default="data/products.db",
        help='Path to database file'
    )
    
    args = parser.parse_args()
    
    logger.info(f"Migrating database: {args.db_path}")
    success = migrate_database(args.db_path)
    
    if success:
        logger.info("\n✅ Migration completed successfully!")
    else:
        logger.error("\n❌ Migration failed!")
        exit(1)
