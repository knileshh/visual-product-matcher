"""
Visual Product Matcher - Flask Application Entry Point

Author: Nilesh Kumar
Email: hey@knileshh.com
Website: https://knileshh.com
GitHub: @knileshh

AI-powered visual search engine for finding similar fashion products
using CLIP embeddings and FAISS similarity search.
"""
import os
import sys
import logging
from pathlib import Path
import yaml
from flask import Flask
from flask_cors import CORS
from threading import Thread
import time
import atexit

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.models import Database
from src.services.image_service import ImageService
from src.services.embedding_service import EmbeddingService
from src.services.search_service import SearchService
from src.routes.api import init_api
from src.routes.ui import init_ui
from src.middleware import init_rate_limiter, init_security_middleware


def load_config(config_path: str = "config.yaml") -> dict:
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config


def setup_logging(config: dict) -> None:
    """Setup application logging."""
    log_config = config['logging']
    log_dir = Path(log_config['log_file']).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, log_config['level']),
        format=log_config['format'],
        handlers=[
            logging.FileHandler(log_config['log_file']),
            logging.StreamHandler()
        ]
    )


# Global variables for cleanup scheduler
cleanup_thread = None
cleanup_running = False


def cleanup_scheduler(image_service: ImageService, interval_minutes: int = 30, max_age_minutes: int = 60):
    """
    Background thread to periodically clean up old uploaded files.
    
    Args:
        image_service: ImageService instance
        interval_minutes: How often to run cleanup (default: 30 minutes)
        max_age_minutes: Age threshold for file deletion (default: 60 minutes)
    """
    global cleanup_running
    logger = logging.getLogger(__name__)
    
    logger.info(f"Upload cleanup scheduler started (interval: {interval_minutes}min, max_age: {max_age_minutes}min)")
    
    while cleanup_running:
        try:
            # Wait for the interval
            time.sleep(interval_minutes * 60)
            
            if not cleanup_running:
                break
            
            # Perform cleanup
            deleted_count = image_service.cleanup_old_uploads(max_age_minutes)
            
            # Also clean temp files
            image_service.cleanup_temp_files()
            
            # Log folder stats
            stats = image_service.get_upload_folder_size()
            logger.info(f"Upload folder: {stats['file_count']} files, {stats['total_size_mb']} MB")
            
        except Exception as e:
            logger.error(f"Error in cleanup scheduler: {str(e)}")


def start_cleanup_scheduler(image_service: ImageService, config: dict):
    """Start the background cleanup scheduler."""
    global cleanup_thread, cleanup_running
    
    cleanup_config = config.get('upload', {}).get('cleanup', {})
    enabled = cleanup_config.get('enabled', True)
    
    if not enabled:
        logging.getLogger(__name__).info("Upload cleanup scheduler is disabled")
        return
    
    interval = cleanup_config.get('interval_minutes', 30)
    max_age = cleanup_config.get('max_age_minutes', 60)
    
    cleanup_running = True
    cleanup_thread = Thread(
        target=cleanup_scheduler,
        args=(image_service, interval, max_age),
        daemon=True
    )
    cleanup_thread.start()


def stop_cleanup_scheduler():
    """Stop the background cleanup scheduler."""
    global cleanup_running, cleanup_thread
    
    if cleanup_thread and cleanup_running:
        logging.getLogger(__name__).info("Stopping cleanup scheduler...")
        cleanup_running = False
        if cleanup_thread.is_alive():
            cleanup_thread.join(timeout=5)


def create_app(config_path: str = "config.yaml") -> Flask:
    """
    Create and configure Flask application.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configured Flask application
    """
    # Load configuration
    config = load_config(config_path)
    
    # Setup logging
    setup_logging(config)
    logger = logging.getLogger(__name__)
    
    # Create Flask app
    app = Flask(__name__)
    app.config['SECRET_KEY'] = config['app']['secret_key']
    app.config['MAX_CONTENT_LENGTH'] = config['upload']['max_file_size_mb'] * 1024 * 1024
    
    # Enable CORS
    CORS(app)
    
    # Initialize security middleware
    init_security_middleware(app, config)
    limiter = init_rate_limiter(app, config)
    
    # Store limiter in app config for use in routes
    app.config['LIMITER'] = limiter
    
    logger.info("Initializing Visual Product Matcher")
    
    try:
        # Initialize database
        logger.info("Initializing database...")
        db = Database(config['database']['path'])
        product_count = db.get_product_count()
        logger.info(f"Database loaded with {product_count} products")
        
        # Initialize services
        logger.info("Initializing services...")
        image_service = ImageService(config)
        embedding_service = EmbeddingService(config)
        search_service = SearchService(config)
        
        # Load or build search index
        if config['index']['rebuild_on_startup']:
            logger.warning("Index rebuild on startup is enabled but not implemented here")
            logger.warning("Run init_data.py to build the index")
        else:
            if search_service.index_exists():
                logger.info("Loading existing search index...")
                if search_service.load_index():
                    logger.info("Search index loaded successfully")
                    index_stats = search_service.get_index_stats()
                    logger.info(f"Index contains {index_stats['num_products']} products")
                else:
                    logger.error("Failed to load search index")
                    logger.warning("Run init_data.py to build the index")
            else:
                logger.warning("Search index not found")
                logger.warning("Run init_data.py to build the index")
        
        # Register blueprints
        api_blueprint = init_api(db, image_service, embedding_service, search_service, config)
        ui_blueprint = init_ui(config)
        
        app.register_blueprint(api_blueprint)
        app.register_blueprint(ui_blueprint)
        
        logger.info("Application initialized successfully")
        
        # Log device info
        device_info = embedding_service.get_device_info()
        logger.info(f"Using device: {device_info['device']}")
        logger.info(f"Model: {device_info['model']}")
        
        # Start cleanup scheduler for uploaded files
        start_cleanup_scheduler(image_service, config)
        
        # Register cleanup on exit
        atexit.register(stop_cleanup_scheduler)
        
    except Exception as e:
        logger.error(f"Error initializing application: {str(e)}", exc_info=True)
        raise
    
    return app


# Error handlers
def register_error_handlers(app: Flask) -> None:
    """Register error handlers."""
    
    @app.errorhandler(404)
    def not_found(error):
        return {"error": "Not found"}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return {"error": "Internal server error"}, 500
    
    @app.errorhandler(413)
    def request_entity_too_large(error):
        return {"error": "File too large"}, 413


if __name__ == "__main__":
    # Create app
    app = create_app()
    register_error_handlers(app)
    
    # Load config for server settings
    config = load_config()
    
    # Run app
    app.run(
        host=config['app']['host'],
        port=config['app']['port'],
        debug=config['app']['debug']
    )
