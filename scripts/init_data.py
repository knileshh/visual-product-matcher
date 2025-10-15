"""
Data initialization script to scan fashion images, generate embeddings, and build FAISS index.
"""
import os
import sys
import logging
from pathlib import Path
from typing import List, Tuple
import yaml
from tqdm import tqdm

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.models import Database, Product
from src.services.embedding_service import EmbeddingService
from src.services.search_service import SearchService
from src.services.image_service import ImageService

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


def scan_images(images_directory: str, supported_formats: List[str]) -> List[str]:
    """
    Scan directory for image files.
    
    Args:
        images_directory: Path to directory containing images
        supported_formats: List of supported file extensions
        
    Returns:
        List of image file paths
    """
    logger.info(f"Scanning images in {images_directory}")
    
    image_paths = set()  # Use set to avoid duplicates
    images_path = Path(images_directory)
    
    if not images_path.exists():
        logger.error(f"Images directory not found: {images_directory}")
        return []
    
    # Scan for images (case-insensitive to avoid duplicates on Windows)
    for ext in supported_formats:
        # Search for both lowercase and uppercase extensions
        # but use a set to deduplicate (Windows filesystem is case-insensitive)
        for pattern in [f"*.{ext}", f"*.{ext.upper()}"]:
            image_paths.update(images_path.rglob(pattern))
    
    image_paths = sorted([str(p) for p in image_paths])  # Sort for consistency
    logger.info(f"Found {len(image_paths)} images")
    
    return image_paths


def extract_product_name(image_path: str) -> str:
    """
    Extract product name from image filename.
    
    Args:
        image_path: Path to image file
        
    Returns:
        Product name
    """
    filename = Path(image_path).stem
    # Replace underscores and hyphens with spaces
    name = filename.replace('_', ' ').replace('-', ' ')
    # Capitalize words
    name = ' '.join(word.capitalize() for word in name.split())
    return name


def extract_category(image_path: str, base_directory: str) -> str:
    """
    Extract category from directory structure.
    
    Args:
        image_path: Path to image file
        base_directory: Base directory path
        
    Returns:
        Category name or 'Uncategorized'
    """
    try:
        # Get relative path from base directory
        rel_path = Path(image_path).relative_to(base_directory)
        
        # If image is in a subdirectory, use first directory as category
        if len(rel_path.parts) > 1:
            category = rel_path.parts[0]
            return category.replace('_', ' ').replace('-', ' ').title()
        
    except ValueError:
        pass
    
    return 'Fashion'


def populate_database(
    db: Database,
    image_paths: List[str],
    images_directory: str,
    image_service: ImageService
) -> List[Tuple[int, str]]:
    """
    Populate database with product metadata.
    
    Args:
        db: Database instance
        image_paths: List of image file paths
        images_directory: Base images directory
        image_service: ImageService instance
        
    Returns:
        List of tuples (product_id, image_path)
    """
    logger.info("Populating database with product metadata")
    
    product_mappings = []
    
    for image_path in tqdm(image_paths, desc="Processing products"):
        try:
            # Normalize path: convert to forward slashes
            normalized_path = str(Path(image_path).as_posix())
            
            # Skip if already exists
            if db.product_exists(normalized_path):
                existing_product = db.get_product_by_path(normalized_path)
                if existing_product:
                    product_mappings.append((existing_product.id, image_path))
                continue
            
            # Extract metadata
            name = extract_product_name(image_path)
            category = extract_category(image_path, images_directory)
            metadata = image_service.get_image_metadata(image_path)
            
            # Create product
            product = Product(
                id=0,  # Will be auto-assigned
                name=name,
                image_path=normalized_path,  # Store normalized path
                category=category,
                file_size=metadata.get('file_size'),
                width=metadata.get('width'),
                height=metadata.get('height'),
                format=metadata.get('format')
            )
            
            # Insert into database
            product_id = db.insert_product(product)
            product_mappings.append((product_id, image_path))
            
        except Exception as e:
            logger.error(f"Error processing {image_path}: {str(e)}")
            continue
    
    logger.info(f"Database populated with {len(product_mappings)} products")
    return product_mappings


def generate_embeddings(
    embedding_service: EmbeddingService,
    product_mappings: List[Tuple[int, str]]
) -> Tuple[List[int], List]:
    """
    Generate embeddings for all products.
    
    Args:
        embedding_service: EmbeddingService instance
        product_mappings: List of (product_id, image_path) tuples
        
    Returns:
        Tuple of (product_ids, embeddings)
    """
    logger.info("Generating embeddings for all products")
    
    product_ids = [pid for pid, _ in product_mappings]
    image_paths = [path for _, path in product_mappings]
    
    # Generate embeddings in batches
    embeddings = embedding_service.generate_embeddings_batch(image_paths)
    
    logger.info(f"Generated embeddings for {len(embeddings)} products")
    return product_ids, embeddings


def build_search_index(
    search_service: SearchService,
    product_ids: List[int],
    embeddings
) -> None:
    """
    Build and save FAISS search index.
    
    Args:
        search_service: SearchService instance
        product_ids: List of product IDs
        embeddings: Array of embeddings
    """
    logger.info("Building FAISS search index")
    
    # Build index
    search_service.build_index(embeddings, product_ids)
    
    # Save index to disk
    search_service.save_index()
    
    logger.info("Search index built and saved successfully")


def main():
    """Main initialization function."""
    try:
        # Load configuration
        config = load_config()
        
        # Initialize services
        logger.info("Initializing services...")
        db = Database(config['database']['path'])
        image_service = ImageService(config)
        embedding_service = EmbeddingService(config)
        search_service = SearchService(config)
        
        # Scan images
        images_directory = config['products']['images_directory']
        supported_formats = config['products']['supported_formats']
        image_paths = scan_images(images_directory, supported_formats)
        
        if not image_paths:
            logger.error("No images found. Exiting.")
            return
        
        # Populate database
        product_mappings = populate_database(
            db, image_paths, images_directory, image_service
        )
        
        if not product_mappings:
            logger.error("No products in database. Exiting.")
            return
        
        # Generate embeddings
        product_ids, embeddings = generate_embeddings(
            embedding_service, product_mappings
        )
        
        # Build search index
        build_search_index(search_service, product_ids, embeddings)
        
        # Print summary
        logger.info("=" * 50)
        logger.info("Data initialization completed successfully!")
        logger.info(f"Total products: {len(product_ids)}")
        logger.info(f"Database: {config['database']['path']}")
        logger.info(f"Index: {config['index']['faiss_index_path']}")
        logger.info("=" * 50)
        
    except Exception as e:
        logger.error(f"Error during initialization: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
