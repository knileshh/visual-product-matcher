"""
Migrate fashion images from local storage to Google Cloud Storage.
This script uploads all images to GCS and updates the database with public URLs.
"""
import os
import sys
import sqlite3
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import logging
from typing import Optional, Tuple
from tqdm import tqdm
from google.cloud import storage
from google.cloud.exceptions import GoogleCloudError
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "data" / "products.db"
IMAGES_DIR = PROJECT_ROOT / "fashion-images" / "fashion-images"

# GCS Configuration
def get_project_id_from_credentials():
    """Extract project ID from credentials file if available."""
    creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', './gcs-credentials.json')
    if os.path.exists(creds_path):
        try:
            with open(creds_path, 'r') as f:
                creds_data = json.load(f)
                return creds_data.get('project_id')
        except Exception:
            pass
    return None

GCS_BUCKET_NAME = os.getenv('GCS_BUCKET_NAME', 'visual-product-matcher-images')
GCS_PROJECT_ID = os.getenv('GCS_PROJECT_ID') or get_project_id_from_credentials()
GCS_BASE_URL = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}"

# Threading
db_lock = Lock()
stats_lock = Lock()
stats = {
    'uploaded': 0,
    'skipped': 0,
    'errors': 0,
    'total': 0
}


def init_gcs_client() -> storage.Client:
    """Initialize Google Cloud Storage client."""
    try:
        # Check for credentials file first
        credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', './gcs-credentials.json')
        
        if os.path.exists(credentials_path):
            logger.info(f"Using credentials from: {credentials_path}")
            client = storage.Client.from_service_account_json(
                credentials_path,
                project=GCS_PROJECT_ID
            )
        else:
            # Fall back to Application Default Credentials
            logger.info("Using Application Default Credentials")
            client = storage.Client(project=GCS_PROJECT_ID)
        
        logger.info(f"GCS Client initialized for project: {GCS_PROJECT_ID}")
        return client
    except Exception as e:
        logger.error(f"Failed to initialize GCS client: {e}")
        logger.error("Make sure you have either:")
        logger.error("  1. gcs-credentials.json file in project root, OR")
        logger.error("  2. Run: gcloud auth application-default login")
        raise


def create_bucket_if_not_exists(client: storage.Client, bucket_name: str, location: str = 'US') -> storage.Bucket:
    """Create GCS bucket if it doesn't exist."""
    try:
        bucket = client.bucket(bucket_name)
        
        if not bucket.exists():
            logger.info(f"Creating bucket: {bucket_name}")
            bucket = client.create_bucket(bucket_name, location=location)
            logger.info(f"Bucket {bucket_name} created in {location}")
        else:
            logger.info(f"Bucket {bucket_name} already exists")
        
        return bucket
    except GoogleCloudError as e:
        logger.error(f"Error with bucket: {e}")
        raise


def make_bucket_public(bucket: storage.Bucket) -> None:
    """Make all objects in bucket publicly readable."""
    try:
        policy = bucket.get_iam_policy(requested_policy_version=3)
        
        # Add allUsers as Storage Object Viewer
        policy.bindings.append({
            "role": "roles/storage.objectViewer",
            "members": {"allUsers"}
        })
        
        bucket.set_iam_policy(policy)
        logger.info(f"Bucket {bucket.name} is now publicly readable")
    except GoogleCloudError as e:
        logger.error(f"Error making bucket public: {e}")
        logger.error("You may need to do this manually in GCP Console")


def get_all_images(images_dir: Path) -> list:
    """Get all image files from directory."""
    image_extensions = {'.jpg', '.jpeg', '.png', '.webp'}
    images = []
    
    if not images_dir.exists():
        logger.error(f"Images directory not found: {images_dir}")
        return images
    
    logger.info(f"Scanning directory: {images_dir}")
    
    for root, dirs, files in os.walk(images_dir):
        for file in files:
            ext = Path(file).suffix.lower()
            if ext in image_extensions:
                full_path = Path(root) / file
                # Get relative path from images_dir
                rel_path = full_path.relative_to(images_dir)
                images.append((full_path, str(rel_path)))
    
    logger.info(f"Found {len(images)} images")
    return images


def get_product_by_image_path(image_path: str) -> Optional[dict]:
    """Get product from database by image path."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Try exact match first
            cursor.execute(
                "SELECT id, image_path, cloudinary_url FROM products WHERE image_path = ?",
                (image_path,)
            )
            result = cursor.fetchone()
            
            if result:
                return dict(result)
            
            # Try partial match (for nested paths)
            cursor.execute(
                "SELECT id, image_path, cloudinary_url FROM products WHERE image_path LIKE ?",
                (f"%{image_path}%",)
            )
            result = cursor.fetchone()
            
            return dict(result) if result else None
            
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        return None


def update_product_gcs_url(product_id: int, gcs_url: str) -> bool:
    """Update product with GCS URL in database."""
    try:
        with db_lock:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                
                # Add gcs_url column if it doesn't exist
                try:
                    cursor.execute("""
                        ALTER TABLE products ADD COLUMN gcs_url TEXT
                    """)
                    logger.info("Added gcs_url column to products table")
                except sqlite3.OperationalError:
                    pass  # Column already exists
                
                # Update the product
                cursor.execute("""
                    UPDATE products 
                    SET cloudinary_url = ?, gcs_url = ?
                    WHERE id = ?
                """, (gcs_url, gcs_url, product_id))
                
                conn.commit()
                return True
                
    except sqlite3.Error as e:
        logger.error(f"Database error updating product {product_id}: {e}")
        return False


def upload_image_to_gcs(
    bucket: storage.Bucket,
    local_path: Path,
    gcs_path: str,
    dry_run: bool = False
) -> Tuple[bool, str]:
    """
    Upload image to Google Cloud Storage.
    
    Args:
        bucket: GCS bucket object
        local_path: Local file path
        gcs_path: Destination path in GCS
        dry_run: If True, don't actually upload
        
    Returns:
        Tuple of (success, gcs_url or error_message)
    """
    try:
        if not local_path.exists():
            return False, f"File not found: {local_path}"
        
        if dry_run:
            gcs_url = f"{GCS_BASE_URL}/{gcs_path}"
            return True, gcs_url
        
        # Create blob with public-read permission
        blob = bucket.blob(gcs_path)
        
        # Set content type based on extension
        content_type = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.webp': 'image/webp'
        }.get(local_path.suffix.lower(), 'image/jpeg')
        
        # Upload file
        blob.upload_from_filename(
            str(local_path),
            content_type=content_type
        )
        
        # Make it publicly accessible (if bucket isn't already public)
        # blob.make_public()  # Optional, only if bucket-level policy isn't set
        
        # Get public URL
        gcs_url = blob.public_url
        
        return True, gcs_url
        
    except GoogleCloudError as e:
        logger.error(f"GCS error uploading {local_path}: {e}")
        return False, str(e)
    except Exception as e:
        logger.error(f"Error uploading {local_path}: {e}")
        return False, str(e)


def process_image(
    bucket: storage.Bucket,
    local_path: Path,
    rel_path: str,
    dry_run: bool = False
) -> Tuple[bool, str]:
    """Process a single image: upload to GCS and update database."""
    
    # Find product in database
    product = get_product_by_image_path(str(rel_path))
    
    if not product:
        # Try with different path formats
        alt_paths = [
            str(rel_path),
            f"fashion-images/{rel_path}",
            f"fashion-images/fashion-images/{rel_path}",
        ]
        
        for alt_path in alt_paths:
            product = get_product_by_image_path(alt_path)
            if product:
                break
    
    if not product:
        with stats_lock:
            stats['skipped'] += 1
        return False, f"Product not found in database: {rel_path}"
    
    # Check if already has GCS URL
    if product.get('cloudinary_url') and 'storage.googleapis.com' in product['cloudinary_url']:
        with stats_lock:
            stats['skipped'] += 1
        return True, "Already has GCS URL"
    
    # Upload to GCS
    gcs_path = f"products/{rel_path}"
    success, gcs_url_or_error = upload_image_to_gcs(bucket, local_path, gcs_path, dry_run)
    
    if not success:
        with stats_lock:
            stats['errors'] += 1
        return False, gcs_url_or_error
    
    # Update database
    if not dry_run:
        if not update_product_gcs_url(product['id'], gcs_url_or_error):
            with stats_lock:
                stats['errors'] += 1
            return False, "Failed to update database"
    
    with stats_lock:
        stats['uploaded'] += 1
    
    return True, gcs_url_or_error


def migrate_images(
    max_workers: int = 10,
    max_uploads: Optional[int] = None,
    dry_run: bool = False,
    project_id: Optional[str] = None,
    bucket_name: Optional[str] = None
):
    """
    Main migration function.
    
    Args:
        max_workers: Number of parallel upload threads
        max_uploads: Maximum number of images to upload (for testing)
        dry_run: If True, simulate without actual uploads
        project_id: GCS project ID (overrides environment)
        bucket_name: GCS bucket name (overrides environment)
    """
    
    # Use provided values or fall back to module-level config
    actual_project_id = project_id or GCS_PROJECT_ID
    actual_bucket_name = bucket_name or GCS_BUCKET_NAME
    
    if not actual_project_id:
        logger.error("=" * 80)
        logger.error("ERROR: GCS_PROJECT_ID not set!")
        logger.error("=" * 80)
        logger.error("Options to fix:")
        logger.error("  1. Use --project-id flag")
        logger.error("  2. Set in .env file: GCS_PROJECT_ID=YOUR_PROJECT_ID")
        logger.error("  3. Ensure gcs-credentials.json exists")
        logger.error("=" * 80)
        return
    
    logger.info("=" * 80)
    logger.info("GCS MIGRATION SCRIPT")
    logger.info("=" * 80)
    logger.info(f"Project ID: {actual_project_id}")
    logger.info(f"Bucket Name: {actual_bucket_name}")
    
    if dry_run:
        logger.info("DRY RUN MODE - No uploads or database changes will be made")
    
    # Get all images
    images = get_all_images(IMAGES_DIR)
    
    if not images:
        logger.error("No images found!")
        return
    
    stats['total'] = len(images)
    
    if max_uploads:
        images = images[:max_uploads]
        logger.info(f"Limiting to {max_uploads} images for testing")
    
    logger.info(f"Found {len(images)} images to process")
    
    # Initialize GCS
    if not dry_run:
        try:
            # Temporarily set environment for client initialization
            os.environ['GCS_PROJECT_ID'] = actual_project_id
            os.environ['GCS_BUCKET_NAME'] = actual_bucket_name
            
            client = init_gcs_client()
            bucket = create_bucket_if_not_exists(client, actual_bucket_name)
            
            # Make bucket public (one-time setup)
            try:
                make_bucket_public(bucket)
            except Exception as e:
                logger.warning(f"Could not set bucket public policy automatically: {e}")
                logger.warning("You may need to make the bucket public manually")
        except Exception as e:
            logger.error(f"Failed to initialize GCS: {e}")
            return
    else:
        bucket = None
    
    # Process images in parallel
    logger.info(f"Starting upload with {max_workers} workers...")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        futures = {
            executor.submit(process_image, bucket, local_path, rel_path, dry_run): (local_path, rel_path)
            for local_path, rel_path in images
        }
        
        # Process results with progress bar
        with tqdm(total=len(futures), desc="Uploading", unit="image") as pbar:
            for future in as_completed(futures):
                local_path, rel_path = futures[future]
                try:
                    success, message = future.result()
                    if not success and not message.startswith("Product not found"):
                        logger.debug(f"{'✓' if success else '✗'} {rel_path}: {message}")
                except Exception as e:
                    logger.error(f"Exception processing {rel_path}: {e}")
                    with stats_lock:
                        stats['errors'] += 1
                finally:
                    pbar.update(1)
    
    # Print summary
    logger.info("=" * 80)
    logger.info("MIGRATION SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Total images found:    {stats['total']}")
    logger.info(f"Successfully uploaded: {stats['uploaded']}")
    logger.info(f"Skipped:              {stats['skipped']}")
    logger.info(f"Errors:               {stats['errors']}")
    logger.info("=" * 80)
    
    if dry_run:
        logger.info("This was a DRY RUN - no actual changes were made")
    else:
        base_url = f"https://storage.googleapis.com/{actual_bucket_name}"
        logger.info(f"Images are now available at: {base_url}/products/")
        logger.info("Update complete! Your app will now serve images from GCS.")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrate images to Google Cloud Storage')
    parser.add_argument('--workers', type=int, default=10, help='Number of parallel workers')
    parser.add_argument('--max-uploads', type=int, help='Maximum number of images to upload (for testing)')
    parser.add_argument('--dry-run', action='store_true', help='Simulate without actual uploads')
    parser.add_argument('--project-id', type=str, help='Google Cloud Project ID (overrides .env)')
    parser.add_argument('--bucket-name', type=str, help='GCS Bucket name (overrides .env)')
    
    args = parser.parse_args()
    
    # Determine project ID and bucket name (args override env/file)
    project_id = args.project_id or GCS_PROJECT_ID
    bucket_name = args.bucket_name or GCS_BUCKET_NAME
    
    # Validate we have required configuration
    if not project_id:
        logger.error("="*80)
        logger.error("ERROR: GCS_PROJECT_ID not set!")
        logger.error("="*80)
        logger.error("Options to fix:")
        logger.error("  1. Use --project-id flag: --project-id YOUR_PROJECT_ID")
        logger.error("  2. Set in .env file: GCS_PROJECT_ID=YOUR_PROJECT_ID")
        logger.error("  3. Ensure gcs-credentials.json exists (auto-detects project ID)")
        logger.error("")
        logger.error(f"Current values:")
        logger.error(f"  From .env: {GCS_PROJECT_ID or 'NOT SET'}")
        logger.error(f"  Bucket: {bucket_name}")
        logger.error(f"  Credentials: {os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'NOT SET')}")
        logger.error("="*80)
        sys.exit(1)
    
    if not bucket_name:
        logger.error("ERROR: GCS_BUCKET_NAME not set!")
        logger.error("Use --bucket-name flag or set GCS_BUCKET_NAME in .env")
        sys.exit(1)
    
    migrate_images(
        max_workers=args.workers,
        max_uploads=args.max_uploads,
        dry_run=args.dry_run,
        project_id=project_id,
        bucket_name=bucket_name
    )
