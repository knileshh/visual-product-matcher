"""
Sync Database with Existing Cloudinary URLs
===========================================
This script fetches URLs from Cloudinary and updates the database.
NO UPLOADS - Only syncs existing URLs to fix the database.
"""

import os
import sys
import sqlite3
import logging
from pathlib import Path
from dotenv import load_dotenv
import cloudinary
import cloudinary.api

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def init_cloudinary():
    """Initialize Cloudinary configuration."""
    load_dotenv()
    
    # Try CLOUDINARY_URL first (single variable format)
    cloudinary_url = os.getenv('CLOUDINARY_URL')
    if cloudinary_url:
        # Parse the URL format: cloudinary://api_key:api_secret@cloud_name
        import re
        match = re.match(r'cloudinary://(\d+):([^@]+)@(.+)', cloudinary_url)
        if match:
            api_key, api_secret, cloud_name = match.groups()
            cloudinary.config(
                cloud_name=cloud_name,
                api_key=api_key,
                api_secret=api_secret,
                secure=True
            )
        else:
            raise ValueError("Invalid CLOUDINARY_URL format")
    else:
        # Fall back to individual variables
        cloudinary.config(
            cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
            api_key=os.getenv('CLOUDINARY_API_KEY'),
            api_secret=os.getenv('CLOUDINARY_API_SECRET'),
            secure=True
        )
    
    logger.info(f"✅ Cloudinary connected - Cloud: {cloudinary.config().cloud_name}")


def fetch_all_cloudinary_urls(folder="visual-product-matcher"):
    """
    Fetch all image URLs from Cloudinary.
    
    Returns:
        dict: Mapping of filename -> cloudinary_url
    """
    logger.info(f"Fetching all images from Cloudinary folder: {folder}")
    
    cloudinary_urls = {}
    next_cursor = None
    page = 1
    
    try:
        while True:
            logger.info(f"  Fetching page {page}...")
            
            params = {
                "type": "upload",
                "prefix": f"{folder}/",
                "max_results": 500
            }
            if next_cursor:
                params["next_cursor"] = next_cursor
            
            result = cloudinary.api.resources(**params)
            resources = result.get('resources', [])
            
            # Extract filename and URL
            for resource in resources:
                filename = resource['public_id'].split('/')[-1] + '.jpg'  # Add extension
                cloudinary_urls[filename] = resource['secure_url']
            
            logger.info(f"    Found {len(resources)} images (Total: {len(cloudinary_urls)})")
            
            next_cursor = result.get('next_cursor')
            if not next_cursor:
                break
            
            page += 1
    
    except Exception as e:
        logger.error(f"Error fetching from Cloudinary: {e}")
        raise
    
    logger.info(f"✅ Fetched {len(cloudinary_urls)} URLs from Cloudinary")
    return cloudinary_urls


def update_database(db_path, cloudinary_urls):
    """
    Update database with Cloudinary URLs using EXACT path matching.
    
    Args:
        db_path: Path to SQLite database
        cloudinary_urls: Dict mapping filename -> cloudinary_url
    """
    logger.info(f"\nUpdating database: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    updated_count = 0
    not_found_count = 0
    
    try:
        # Check database structure
        cursor.execute("PRAGMA table_info(products)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'cloudinary_url' not in columns:
            logger.error("❌ Database missing 'cloudinary_url' column!")
            logger.error("   Run migrate_db.py first to add the column.")
            return
        
        # Get all products that need URLs
        cursor.execute("""
            SELECT id, image_path 
            FROM products 
            WHERE cloudinary_url IS NULL OR cloudinary_url = ''
        """)
        products_needing_urls = cursor.fetchall()
        
        logger.info(f"Found {len(products_needing_urls)} products needing Cloudinary URLs")
        
        # Update each product
        for product_id, image_path in products_needing_urls:
            # Extract filename from path
            filename = Path(image_path).name
            
            # Look up Cloudinary URL
            if filename in cloudinary_urls:
                cloudinary_url = cloudinary_urls[filename]
                
                # Update database with EXACT match (fixed SQL query)
                cursor.execute(
                    """UPDATE products 
                       SET cloudinary_url = ?
                       WHERE id = ?""",
                    (cloudinary_url, product_id)
                )
                updated_count += 1
                
                if updated_count % 1000 == 0:
                    logger.info(f"  Updated {updated_count} products...")
            else:
                not_found_count += 1
                if not_found_count <= 10:  # Show first 10 missing
                    logger.warning(f"  No Cloudinary URL found for: {filename}")
        
        conn.commit()
        
        logger.info("\n" + "="*60)
        logger.info("SYNC SUMMARY")
        logger.info("="*60)
        logger.info(f"✅ Updated: {updated_count} products")
        if not_found_count > 0:
            logger.warning(f"⚠️  Not found on Cloudinary: {not_found_count} products")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"Database error: {e}")
        raise
    finally:
        conn.close()


def verify_database(db_path):
    """
    Verify database state after sync.
    
    Args:
        db_path: Path to SQLite database
    """
    logger.info("\nVerifying database state...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Total products
        cursor.execute("SELECT COUNT(*) FROM products")
        total = cursor.fetchone()[0]
        
        # Products with URLs
        cursor.execute("SELECT COUNT(*) FROM products WHERE cloudinary_url IS NOT NULL AND cloudinary_url != ''")
        with_urls = cursor.fetchone()[0]
        
        # Unique URLs
        cursor.execute("SELECT COUNT(DISTINCT cloudinary_url) FROM products WHERE cloudinary_url IS NOT NULL AND cloudinary_url != ''")
        unique_urls = cursor.fetchone()[0]
        
        logger.info(f"\nDatabase Statistics:")
        logger.info(f"  Total products: {total}")
        logger.info(f"  Products with Cloudinary URL: {with_urls}")
        logger.info(f"  Unique Cloudinary URLs: {unique_urls}")
        
        if unique_urls == with_urls:
            logger.info(f"  ✅ Perfect! Each product has a unique URL")
        else:
            logger.warning(f"  ⚠️  Mismatch: {with_urls - unique_urls} products share URLs")
        
    finally:
        conn.close()


def main():
    """Main sync function."""
    print("\n" + "="*60)
    print("CLOUDINARY URL SYNC TOOL")
    print("="*60)
    print("This script will:")
    print("  1. Fetch all existing URLs from Cloudinary")
    print("  2. Update database with correct URLs")
    print("  3. NO UPLOADS - Only syncing existing data")
    print("="*60 + "\n")
    
    # Database path
    db_path = "data/products.db"
    
    if not Path(db_path).exists():
        logger.error(f"❌ Database not found: {db_path}")
        sys.exit(1)
    
    try:
        # Step 1: Initialize Cloudinary
        init_cloudinary()
        
        # Step 2: Fetch all URLs from Cloudinary
        cloudinary_urls = fetch_all_cloudinary_urls()
        
        # Step 3: Update database
        update_database(db_path, cloudinary_urls)
        
        # Step 4: Verify
        verify_database(db_path)
        
        logger.info("\n✅ Sync complete!")
        
    except Exception as e:
        logger.error(f"\n❌ Sync failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
