"""
API routes for Visual Product Matcher.
"""
import os
import logging
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import tempfile
from src.middleware import validate_url_safety, validate_file_upload

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__, url_prefix='/api')


def init_api(
    db,
    image_service,
    embedding_service,
    search_service,
    config
):
    """
    Initialize API routes with dependencies.
    
    Args:
        db: Database instance
        image_service: ImageService instance
        embedding_service: EmbeddingService instance
        search_service: SearchService instance
        config: Configuration dictionary
    """
    
    @api_bp.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint."""
        try:
            # Check database
            db_status = db.get_product_count() >= 0
            
            # Check search index
            index_stats = search_service.get_index_stats()
            index_status = index_stats.get('status') == 'loaded'
            
            # Check embedding service
            device_info = embedding_service.get_device_info()
            
            return jsonify({
                'status': 'healthy' if (db_status and index_status) else 'degraded',
                'database': {
                    'status': 'ok' if db_status else 'error',
                    'product_count': db.get_product_count()
                },
                'search_index': index_stats,
                'embedding_service': device_info
            }), 200
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return jsonify({
                'status': 'unhealthy',
                'error': str(e)
            }), 500
    
    @api_bp.route('/upload', methods=['POST'])
    def upload_and_search():
        """
        Upload image and search for similar products.
        
        Expects:
            - file: Image file (multipart/form-data)
            - k: Optional number of results (default from config)
            - threshold: Optional similarity threshold (0-1)
        
        Rate limited to prevent abuse.
        """
        # Get rate limiter and apply upload-specific limit
        limiter = current_app.config.get('LIMITER')
        if limiter:
            upload_limit = config.get('security', {}).get('rate_limit', {}).get('upload', '10 per minute')
            try:
                limiter.limit(upload_limit)(lambda: None)()
            except Exception as e:
                logger.warning(f"Rate limit exceeded for upload: {e}")
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'message': 'Too many upload requests. Please try again later.'
                }), 429
        
        try:
            # Check if file is present
            if 'file' not in request.files:
                return jsonify({
                    'error': 'No file provided',
                    'message': 'Please upload an image file'
                }), 400
            
            file = request.files['file']
            
            if file.filename == '':
                return jsonify({
                    'error': 'Empty filename',
                    'message': 'Please select a file'
                }), 400
            
            # Validate file security
            is_valid, error_message = validate_file_upload(file, config)
            if not is_valid:
                logger.warning(f"File validation failed: {error_message}")
                return jsonify({
                    'error': 'Invalid file',
                    'message': error_message
                }), 400
            
            # Get optional parameters
            k = request.form.get('k', config['search']['default_k'], type=int)
            threshold = request.form.get(
                'threshold',
                config['search']['default_similarity_threshold'],
                type=float
            )
            
            # Validate parameters
            if k < 1 or k > 100:
                return jsonify({
                    'error': 'Invalid k parameter',
                    'message': 'k must be between 1 and 100'
                }), 400
            
            if threshold < 0 or threshold > 1:
                return jsonify({
                    'error': 'Invalid threshold parameter',
                    'message': 'threshold must be between 0 and 1'
                }), 400
            
            # Process uploaded file
            success, error, file_path = image_service.process_uploaded_file(
                file,
                secure_filename(file.filename)
            )
            
            if not success:
                return jsonify({
                    'error': 'File upload failed',
                    'message': error
                }), 400
            
            # Generate embedding for uploaded image
            query_embedding = embedding_service.generate_embedding(file_path)
            
            if query_embedding is None:
                return jsonify({
                    'error': 'Embedding generation failed',
                    'message': 'Could not process the uploaded image'
                }), 500
            
            # Search for similar products
            results = search_service.search(
                query_embedding,
                k=k,
                similarity_threshold=threshold
            )
            
            # Get product details for results
            products = []
            for product_id, similarity in results:
                product = db.get_product_by_id(product_id)
                if product:
                    # Use Cloudinary URL if available, fallback to local path
                    image_url = product.cloudinary_url if product.cloudinary_url else product.image_path
                    
                    products.append({
                        'id': product.id,
                        'name': product.name,
                        'category': product.category,
                        'image_path': image_url,  # Now contains Cloudinary URL
                        'similarity': round(similarity, 4),
                        'width': product.width,
                        'height': product.height
                    })
            
            return jsonify({
                'success': True,
                'query_image': file_path,
                'results_count': len(products),
                'products': products,
                'parameters': {
                    'k': k,
                    'threshold': threshold
                }
            }), 200
            
        except Exception as e:
            logger.error(f"Error in upload_and_search: {str(e)}", exc_info=True)
            return jsonify({
                'error': 'Internal server error',
                'message': str(e)
            }), 500
    
    @api_bp.route('/search-url', methods=['POST'])
    def search_by_url():
        """
        Search for similar products using image URL.
        
        Expects JSON:
            - url: Image URL
            - k: Optional number of results
            - threshold: Optional similarity threshold
        
        Rate limited and validates URLs for security.
        """
        # Apply search rate limit
        limiter = current_app.config.get('LIMITER')
        if limiter:
            search_limit = config.get('security', {}).get('rate_limit', {}).get('search', '30 per minute')
            try:
                limiter.limit(search_limit)(lambda: None)()
            except Exception as e:
                logger.warning(f"Rate limit exceeded for search: {e}")
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'message': 'Too many search requests. Please try again later.'
                }), 429
        
        try:
            data = request.get_json()
            
            if not data or 'url' not in data:
                return jsonify({
                    'error': 'Missing URL',
                    'message': 'Please provide an image URL'
                }), 400
            
            url = data['url']
            
            # Validate URL security (prevent SSRF)
            is_valid, error_message = validate_url_safety(url, config)
            if not is_valid:
                logger.warning(f"URL validation failed: {error_message} - URL: {url}")
                return jsonify({
                    'error': 'Invalid URL',
                    'message': error_message
                }), 400
            
            k = data.get('k', config['search']['default_k'])
            threshold = data.get('threshold', config['search']['default_similarity_threshold'])
            
            # Validate parameters
            if k < 1 or k > 100:
                return jsonify({
                    'error': 'Invalid k parameter',
                    'message': 'k must be between 1 and 100'
                }), 400
            
            if threshold < 0 or threshold > 1:
                return jsonify({
                    'error': 'Invalid threshold parameter',
                    'message': 'threshold must be between 0 and 1'
                }), 400
            
            # Download image from URL
            temp_path = os.path.join(
                tempfile.gettempdir(),
                f"query_{secure_filename(os.path.basename(url))}"
            )
            
            success, error = image_service.download_image_from_url(url, temp_path)
            
            if not success:
                return jsonify({
                    'error': 'Image download failed',
                    'message': error
                }), 400
            
            # Generate embedding
            query_embedding = embedding_service.generate_embedding(temp_path)
            
            if query_embedding is None:
                return jsonify({
                    'error': 'Embedding generation failed',
                    'message': 'Could not process the image from URL'
                }), 500
            
            # Search for similar products
            results = search_service.search(
                query_embedding,
                k=k,
                similarity_threshold=threshold
            )
            
            # Get product details
            products = []
            for product_id, similarity in results:
                product = db.get_product_by_id(product_id)
                if product:
                    # Use Cloudinary URL if available, fallback to local path
                    image_url = product.cloudinary_url if product.cloudinary_url else product.image_path
                    
                    products.append({
                        'id': product.id,
                        'name': product.name,
                        'category': product.category,
                        'image_path': image_url,  # Now contains Cloudinary URL
                        'similarity': round(similarity, 4),
                        'width': product.width,
                        'height': product.height
                    })
            
            # Cleanup temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            return jsonify({
                'success': True,
                'query_url': url,
                'results_count': len(products),
                'products': products,
                'parameters': {
                    'k': k,
                    'threshold': threshold
                }
            }), 200
            
        except Exception as e:
            logger.error(f"Error in search_by_url: {str(e)}", exc_info=True)
            return jsonify({
                'error': 'Internal server error',
                'message': str(e)
            }), 500
    
    @api_bp.route('/products/<int:product_id>', methods=['GET'])
    def get_product(product_id):
        """Get product details by ID."""
        try:
            product = db.get_product_by_id(product_id)
            
            if not product:
                return jsonify({
                    'error': 'Product not found',
                    'message': f'No product with ID {product_id}'
                }), 404
            
            # Use Cloudinary URL if available, fallback to local path
            image_url = product.cloudinary_url if product.cloudinary_url else product.image_path
            
            return jsonify({
                'id': product.id,
                'name': product.name,
                'category': product.category,
                'image_path': image_url,  # Now contains Cloudinary URL
                'file_size': product.file_size,
                'width': product.width,
                'height': product.height,
                'format': product.format,
                'created_at': str(product.created_at) if product.created_at else None
            }), 200
            
        except Exception as e:
            logger.error(f"Error in get_product: {str(e)}")
            return jsonify({
                'error': 'Internal server error',
                'message': str(e)
            }), 500
    
    @api_bp.route('/stats', methods=['GET'])
    def get_stats():
        """Get application statistics."""
        try:
            product_count = db.get_product_count()
            index_stats = search_service.get_index_stats()
            device_info = embedding_service.get_device_info()
            
            return jsonify({
                'products': {
                    'total': product_count
                },
                'search_index': index_stats,
                'ml_config': device_info
            }), 200
            
        except Exception as e:
            logger.error(f"Error in get_stats: {str(e)}")
            return jsonify({
                'error': 'Internal server error',
                'message': str(e)
            }), 500
    
    return api_bp
