"""
Upload fashion images to Cloudinary.
This script uploads all images from the fashion-images directory to Cloudinary
and updates the database with the new cloud URLs.
"""
import os
import sys
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import time

# Load environment variables FIRST before importing cloudinary
from dotenv import load_dotenv
load_dotenv()

# Configure urllib3 connection pool before importing cloudinary
import urllib3
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import requests

# Now import cloudinary (it will read CLOUDINARY_URL from environment)
import cloudinary
import cloudinary.uploader
import cloudinary.api
from tqdm import tqdm
import yaml

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.models import Database

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_config(config_path: str = "config.yaml") -> dict:
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config


def init_cloudinary():
    """Initialize Cloudinary configuration from environment."""
    cloudinary_url = os.getenv('CLOUDINARY_URL')
    
    if not cloudinary_url:
        raise ValueError(
            "CLOUDINARY_URL not found in environment variables. "
            "Please set it in your .env file."
        )
    
    # Cloudinary automatically reads from CLOUDINARY_URL environment variable
    # but we need to ensure config() is called to parse it
    config = cloudinary.config()
    
    # Verify configuration was loaded
    if not config.cloud_name:
        raise ValueError(
            "Cloudinary configuration failed to load. "
            f"Check CLOUDINARY_URL format: cloudinary://api_key:api_secret@cloud_name"
        )
    
    # Configure connection pooling for better performance
    # Increase pool size to support more parallel connections
    import urllib3.util.connection as urllib_connection
    
    # Increase the default connection pool size
    adapter = HTTPAdapter(
        pool_connections=20,  # Number of connection pools
        pool_maxsize=20,      # Max connections per pool
        max_retries=Retry(
            total=3,
            backoff_factor=0.3,
            status_forcelist=[500, 502, 503, 504]
        )
    )
    
    # Apply to cloudinary's session if it exists
    try:
        if hasattr(cloudinary, 'http_session'):
            cloudinary.http_session.mount('https://', adapter)
            cloudinary.http_session.mount('http://', adapter)
    except:
        pass  # Cloudinary might not expose http_session
    
    logger.info(f"Cloudinary configuration loaded - Cloud: {config.cloud_name}")
    logger.info(f"Connection pool configured for high-performance uploads")
    return cloudinary_url


def get_all_images(images_dir: str) -> list:
    """
    Get all image files from the fashion-images directory.
    Handles nested folder structure and avoids case-insensitive duplicates.
    
    Args:
        images_dir: Path to images directory
        
    Returns:
        List of unique image file paths
    """
    images_dir = Path(images_dir)
    
    # Handle nested fashion-images/fashion-images structure
    if images_dir.name == "fashion-images" and (images_dir / "fashion-images").exists():
        images_dir = images_dir / "fashion-images"
        logger.info(f"Using nested directory: {images_dir}")
    
    supported_formats = ['.jpg', '.jpeg', '.png', '.webp']
    
    # Use set to avoid duplicates from the start
    image_files = set()
    
    # Only scan with lowercase extensions to avoid double counting
    for format_ext in supported_formats:
        # Use glob (not rglob) since we're already in the nested folder
        for img_path in images_dir.glob(f'*{format_ext}'):
            # Store the actual path (preserve case)
            image_files.add(img_path)
        # Also check uppercase but add to same set (deduplicates automatically)
        for img_path in images_dir.glob(f'*{format_ext.upper()}'):
            image_files.add(img_path)
    
    # Convert set to list and sort for consistent ordering
    image_files = sorted(list(image_files))
    
    logger.info(f"Found {len(image_files)} unique images in {images_dir}")
    return image_files


def upload_image_to_cloudinary(
    image_path: Path,
    folder: str = "visual-product-matcher",
    overwrite: bool = False
) -> dict:
    """
    Upload a single image to Cloudinary.
    
    Args:
        image_path: Path to image file
        folder: Cloudinary folder name
        overwrite: Whether to overwrite existing images
        
    Returns:
        Upload response dict with url, secure_url, public_id, etc.
    """
    try:
        # Use filename without extension as public_id
        public_id = image_path.stem
        
        # Upload with options
        response = cloudinary.uploader.upload(
            str(image_path),
            folder=folder,
            public_id=public_id,
            overwrite=overwrite,
            resource_type="image",
            # Optimize settings
            quality="auto:good",
            fetch_format="auto",
            # Tags for organization
            tags=["fashion", "product"]
        )
        
        return response
    
    except Exception as e:
        logger.error(f"Error uploading {image_path.name}: {e}")
        return None


def upload_images_parallel(
    image_files: list,
    folder: str = "visual-product-matcher",
    max_workers: int = 10,
    dry_run: bool = False,
    skip_existing: set = None,
    rate_limit: float = 0.1  # Minimum seconds between uploads per worker
) -> dict:
    """
    Upload multiple images to Cloudinary in parallel using threads.
    
    Args:
        image_files: List of image file paths
        folder: Cloudinary folder name
        max_workers: Number of parallel upload threads (max 10 recommended)
        dry_run: If True, simulate uploads without actually uploading
        skip_existing: Set of image names to skip
        rate_limit: Minimum seconds between uploads per worker (0.1 = 10/sec per worker)
        
    Returns:
        Dict mapping local paths to Cloudinary responses
    """
    upload_results = {}
    failed_uploads = []
    skipped_count = 0
    
    # Thread-safe lock for updating results
    results_lock = Lock()
    
    # Progress bar
    pbar = tqdm(total=len(image_files), desc="Uploading images", unit="img")
    
    def upload_single_image(img_path: Path):
        """Upload a single image with thread-safe result storage."""
        nonlocal skipped_count
        
        # Check if should skip
        if skip_existing and img_path.stem in skip_existing:
            with results_lock:
                skipped_count += 1
                pbar.update(1)
            return
        
        if dry_run:
            logger.info(f"[DRY RUN] Would upload: {img_path.name}")
            with results_lock:
                upload_results[str(img_path)] = {
                    'secure_url': f'https://res.cloudinary.com/CLOUD/image/upload/{folder}/{img_path.stem}.jpg',
                    'bytes': img_path.stat().st_size
                }
                pbar.update(1)
            return
        
        # Actual upload
        response = upload_image_to_cloudinary(img_path, folder=folder)
        
        with results_lock:
            if response:
                upload_results[str(img_path)] = response
            else:
                failed_uploads.append(str(img_path))
            pbar.update(1)
        
        # Optional rate limiting per worker (prevents overwhelming the API)
        if rate_limit > 0 and not dry_run:
            time.sleep(rate_limit)
    
    # Use ThreadPoolExecutor for parallel uploads
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all upload tasks
        futures = [executor.submit(upload_single_image, img_path) for img_path in image_files]
        
        # Wait for all to complete
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                logger.error(f"Thread error: {e}")
    
    pbar.close()
    
    # Return results
    return {
        'upload_results': upload_results,
        'failed_uploads': failed_uploads,
        'skipped_count': skipped_count,
        'success_count': len(upload_results),
        'total_count': len(image_files)
    }


def update_database_with_cloud_urls(
    db: Database,
    upload_results: dict,
    dry_run: bool = False
):
    """
    Update database with Cloudinary URLs.
    
    Args:
        db: Database instance
        upload_results: Dict mapping local paths to Cloudinary responses
        dry_run: If True, don't actually update database
    """
    logger.info("Updating database with Cloudinary URLs...")
    
    updated_count = 0
    
    # Connect to database
    import sqlite3
    conn = sqlite3.connect(db.db_path)
    cursor = conn.cursor()
    
    try:
        for local_path, cloudinary_response in upload_results.items():
            if not cloudinary_response:
                continue
            
            # Get the image filename
            filename = Path(local_path).name
            
            # Find products by exact filename match (not substring match)
            # This prevents "1000.jpg" from matching "10000.jpg", "21000.jpg", etc.
            cursor.execute(
                """SELECT id, image_path FROM products 
                   WHERE image_path LIKE ? 
                   OR image_path LIKE ?
                   OR image_path = ?""",
                (f"%/{filename}", f"%\\{filename}", filename)
            )
            products = cursor.fetchall()
            
            if not products:
                logger.warning(f"No product found for {filename}")
                continue
            
            # Get Cloudinary URL
            cloudinary_url = cloudinary_response.get('secure_url')
            
            for product_id, current_path in products:
                if not dry_run:
                    # Check if columns exist (in case migration wasn't run)
                    cursor.execute("PRAGMA table_info(products)")
                    columns = [col[1] for col in cursor.fetchall()]
                    
                    if 'cloudinary_url' in columns and 'local_image_path' in columns:
                        # Use new columns if available
                        cursor.execute(
                            """UPDATE products 
                               SET cloudinary_url = ?, local_image_path = ?
                               WHERE id = ?""",
                            (cloudinary_url, current_path, product_id)
                        )
                    else:
                        # Fall back to just updating image_path
                        logger.warning(
                            "Database migration not run. "
                            "Run migrate_db.py to add cloudinary_url columns."
                        )
                        cursor.execute(
                            """UPDATE products 
                               SET image_path = ?
                               WHERE id = ?""",
                            (cloudinary_url, product_id)
                        )
                    
                    updated_count += 1
                else:
                    logger.info(f"[DRY RUN] Would update product {product_id} with URL: {cloudinary_url}")
        
        if not dry_run:
            conn.commit()
            logger.info(f"✅ Updated {updated_count} products in database")
        else:
            logger.info(f"[DRY RUN] Would update {updated_count} products")
    
    finally:
        conn.close()
    
    return updated_count


def main(
    batch_size: int = 50,
    max_uploads: int = None,
    dry_run: bool = False,
    skip_existing: bool = True,
    max_workers: int = 10,
    rate_limit: float = 0.05
):
    """
    Main upload function with parallel processing.
    
    Args:
        batch_size: Not used (kept for compatibility)
        max_uploads: Maximum number of images to upload (None = all)
        dry_run: If True, don't actually upload or update database
        skip_existing: If True, skip images already on Cloudinary
        max_workers: Number of parallel upload threads (1-15, default 10)
        rate_limit: Minimum seconds between uploads per worker
    """
    # Initialize
    init_cloudinary()
    config = load_config()
    db = Database(config['database']['path'])
    
    # Get all images
    images_dir = config['products']['images_directory']
    
    # Handle the nested fashion-images/fashion-images structure
    if images_dir == ".":
        images_dir = "fashion-images"
    
    logger.info(f"Scanning images from: {images_dir}")
    image_files = get_all_images(images_dir)
    
    if max_uploads:
        image_files = image_files[:max_uploads]
        logger.info(f"Limiting to first {max_uploads} images")
    
    # Check what's already uploaded (optional)
    existing_images = set()
    if skip_existing:
        try:
            logger.info("Checking existing images on Cloudinary...")
            # Check first 500, then paginate if needed
            all_resources = []
            next_cursor = None
            
            while True:
                params = {
                    "type": "upload",
                    "prefix": "visual-product-matcher/",
                    "max_results": 500
                }
                if next_cursor:
                    params["next_cursor"] = next_cursor
                
                result = cloudinary.api.resources(**params)
                all_resources.extend(result.get('resources', []))
                
                next_cursor = result.get('next_cursor')
                if not next_cursor:
                    break
            
            existing_images = {
                r['public_id'].split('/')[-1] for r in all_resources
            }
            logger.info(f"Found {len(existing_images)} existing images on Cloudinary")
        except Exception as e:
            logger.warning(f"Could not check existing images: {e}")
    
    # Confirmation for large uploads
    if not dry_run and len(image_files) > 100:
        print(f"\n⚠️  About to upload {len(image_files)} images to Cloudinary")
        print(f"   Using {max_workers} parallel workers")
        estimated_time = len(image_files) / (max_workers * 8)  # ~8 images per second with 8 workers
        print(f"   Estimated time: ~{estimated_time/60:.1f} minutes")
        response = input("\nContinue? (y/n): ")
        if response.lower() != 'y':
            logger.info("Upload cancelled by user")
            return
    
    logger.info(f"Starting parallel upload with {max_workers} workers...")
    start_time = time.time()
    
    # Upload images in parallel
    results = upload_images_parallel(
        image_files=image_files,
        folder="visual-product-matcher",
        max_workers=max_workers,
        dry_run=dry_run,
        skip_existing=existing_images,
        rate_limit=rate_limit
    )
    
    upload_results = results['upload_results']
    failed_uploads = results['failed_uploads']
    skipped_count = results['skipped_count']
    
    elapsed_time = time.time() - start_time
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("UPLOAD SUMMARY")
    logger.info("="*60)
    logger.info(f"Total images: {len(image_files)}")
    logger.info(f"Skipped (already uploaded): {skipped_count}")
    logger.info(f"Successfully uploaded: {len(upload_results)}")
    logger.info(f"Failed: {len(failed_uploads)}")
    logger.info(f"Time elapsed: {elapsed_time:.1f} seconds ({elapsed_time/60:.1f} minutes)")
    
    if len(upload_results) > 0:
        upload_rate = len(upload_results) / elapsed_time
        logger.info(f"Upload rate: {upload_rate:.2f} images/second")
    
    if failed_uploads:
        logger.warning(f"\nFailed uploads:")
        for path in failed_uploads[:10]:  # Show first 10
            logger.warning(f"  - {path}")
        if len(failed_uploads) > 10:
            logger.warning(f"  ... and {len(failed_uploads) - 10} more")
    
    # Update database
    if upload_results and not dry_run:
        logger.info("\nUpdating database with Cloudinary URLs...")
        update_database_with_cloud_urls(db, upload_results, dry_run=False)
    
    logger.info("\n✅ Upload completed!")
    
    # Cost estimate
    if not dry_run and upload_results:
        estimated_storage = len(upload_results) * 0.5  # Assume 500KB average
        logger.info(f"\nEstimated storage used: {estimated_storage:.2f} MB")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Upload fashion images to Cloudinary with parallel processing"
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=50,
        help='(Deprecated) Kept for compatibility'
    )
    parser.add_argument(
        '--max-uploads',
        type=int,
        default=None,
        help='Maximum number of images to upload (for testing)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulate upload without actually uploading'
    )
    parser.add_argument(
        '--no-skip-existing',
        action='store_true',
        help='Re-upload images that already exist on Cloudinary'
    )
    parser.add_argument(
        '--workers',
        type=int,
        default=10,
        help='Number of parallel upload threads (1-15, default: 10 for ~10 img/sec)'
    )
    parser.add_argument(
        '--rate-limit',
        type=float,
        default=0.05,
        help='Minimum seconds between uploads per worker (default: 0.05, use 0 for no limit)'
    )
    
    args = parser.parse_args()
    
    # Validate workers
    if args.workers < 1 or args.workers > 15:
        print("⚠️  Warning: workers should be between 1-15. Using default 10.")
        args.workers = 10
    
    main(
        batch_size=args.batch_size,
        max_uploads=args.max_uploads,
        dry_run=args.dry_run,
        skip_existing=not args.no_skip_existing,
        max_workers=args.workers,
        rate_limit=args.rate_limit
    )
