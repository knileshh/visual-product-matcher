"""
Fix remaining products with old Cloudinary URLs by uploading to GCS.
This script targets only products that don't have GCS URLs yet.
"""
import os
import sys
import sqlite3
import logging
from google.cloud import storage
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from threading import Lock
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
DB_PATH = "data/products.db"
IMAGE_DIR = "fashion-images/fashion-images"
GCS_BUCKET_NAME = "visual-product-matcher-images"

# Thread-safe stats and locks
stats = {'uploaded': 0, 'errors': 0}
stats_lock = Lock()
db_lock = Lock()


def get_products_with_old_urls():
    """Get all products that still have old Cloudinary URLs."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, image_path, cloudinary_url 
        FROM products 
        WHERE cloudinary_url NOT LIKE '%storage.googleapis.com%'
    """)
    
    products = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return products


def upload_and_update(bucket, product):
    """Upload image and update database for a single product."""
    try:
        product_id = product['id']
        image_path = product['image_path']
        
        # Get filename from image_path
        filename = os.path.basename(image_path)
        local_path = os.path.join(IMAGE_DIR, filename)
        
        # Check if file exists
        if not os.path.exists(local_path):
            logger.warning(f"File not found: {local_path}")
            with stats_lock:
                stats['errors'] += 1
            return
        
        # Upload to GCS
        gcs_path = f"products/{filename}"
        blob = bucket.blob(gcs_path)
        
        # Check if already exists in GCS
        if blob.exists():
            # Already uploaded, just update database
            gcs_url = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{gcs_path}"
        else:
            # Upload the file
            blob.upload_from_filename(
                local_path,
                content_type='image/jpeg',
                timeout=300
            )
            # Bucket is already public, no need to make_public()
            gcs_url = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{gcs_path}"
        
        # Update database
        with db_lock:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE products SET cloudinary_url = ? WHERE id = ?",
                (gcs_url, product_id)
            )
            conn.commit()
            conn.close()
        
        with stats_lock:
            stats['uploaded'] += 1
        
    except Exception as e:
        logger.error(f"Error processing product {product.get('id')}: {str(e)}")
        with stats_lock:
            stats['errors'] += 1


def main():
    logger.info("="*80)
    logger.info("FIX REMAINING CLOUDINARY URLS")
    logger.info("="*80)
    
    # Get products with old URLs
    logger.info("Finding products with old Cloudinary URLs...")
    products = get_products_with_old_urls()
    logger.info(f"Found {len(products)} products to fix")
    
    if not products:
        logger.info("✅ All products already have GCS URLs!")
        return
    
    # Initialize GCS client
    logger.info(f"Connecting to GCS bucket: {GCS_BUCKET_NAME}")
    
    # Get credentials path
    creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', './gcs-credentials.json')
    if os.path.exists(creds_path):
        logger.info(f"Using credentials from: {creds_path}")
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
    
    storage_client = storage.Client()
    bucket = storage_client.bucket(GCS_BUCKET_NAME)
    
    # Process products with progress bar
    logger.info(f"Processing {len(products)} products with 20 workers...")
    
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [
            executor.submit(upload_and_update, bucket, product)
            for product in products
        ]
        
        # Show progress
        for _ in tqdm(as_completed(futures), total=len(products), desc="Fixing", unit="product"):
            pass
    
    # Summary
    logger.info("="*80)
    logger.info("SUMMARY")
    logger.info("="*80)
    logger.info(f"Total products: {len(products)}")
    logger.info(f"Successfully updated: {stats['uploaded']}")
    logger.info(f"Errors: {stats['errors']}")
    logger.info("="*80)
    
    if stats['errors'] == 0:
        logger.info("✅ All products now have GCS URLs!")
    else:
        logger.warning(f"⚠️ {stats['errors']} products had errors")


if __name__ == "__main__":
    main()
