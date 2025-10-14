"""
Security middleware for Visual Product Matcher.
Implements rate limiting, request validation, and security headers.
"""
import logging
import ipaddress
from functools import wraps
from urllib.parse import urlparse
from flask import request, jsonify, make_response
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from typing import Optional, Callable, Any
import re

logger = logging.getLogger(__name__)


def init_rate_limiter(app, config: dict) -> Optional[Limiter]:
    """
    Initialize rate limiter with configuration.
    
    Args:
        app: Flask application instance
        config: Security configuration dictionary
    
    Returns:
        Limiter instance or None if disabled
    """
    rate_limit_config = config.get('security', {}).get('rate_limit', {})
    
    if not rate_limit_config.get('enabled', False):
        logger.info("Rate limiting is disabled")
        return None
    
    try:
        limiter = Limiter(
            app=app,
            key_func=get_remote_address,
            storage_uri=rate_limit_config.get('storage_uri', 'memory://'),
            default_limits=[rate_limit_config.get('default', '100 per hour')],
            headers_enabled=True,
            swallow_errors=True  # Don't crash app if rate limiter fails
        )
        
        logger.info(
            f"Rate limiter initialized with default limit: "
            f"{rate_limit_config.get('default')}"
        )
        return limiter
    
    except Exception as e:
        logger.error(f"Failed to initialize rate limiter: {e}")
        return None


def validate_url_safety(url: str, config: dict) -> tuple[bool, Optional[str]]:
    """
    Validate URL for security concerns (SSRF prevention).
    
    Args:
        url: URL to validate
        config: Security configuration dictionary
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    validation_config = config.get('security', {}).get('request_validation', {})
    
    # Check URL length
    max_length = validation_config.get('max_url_length', 2048)
    if len(url) > max_length:
        return False, f"URL exceeds maximum length of {max_length} characters"
    
    # Parse URL
    try:
        parsed = urlparse(url)
    except Exception as e:
        return False, f"Invalid URL format: {str(e)}"
    
    # Check scheme
    allowed_schemes = validation_config.get('allowed_url_schemes', ['http', 'https'])
    if parsed.scheme not in allowed_schemes:
        return False, f"URL scheme must be one of: {', '.join(allowed_schemes)}"
    
    # Check for private IPs (SSRF prevention)
    if validation_config.get('blocked_private_ips', True):
        hostname = parsed.hostname
        if hostname:
            # Check if it's an IP address
            try:
                ip = ipaddress.ip_address(hostname)
                if ip.is_private or ip.is_loopback or ip.is_link_local:
                    return False, "Access to private IP addresses is not allowed"
            except ValueError:
                # Not an IP address, check for localhost
                if hostname.lower() in ['localhost', '127.0.0.1', '::1', '0.0.0.0']:
                    return False, "Access to localhost is not allowed"
                
                # Check for suspicious patterns
                suspicious_patterns = [
                    r'169\.254\.',  # Link-local
                    r'metadata\.google\.internal',  # Cloud metadata
                    r'.*\.internal$',  # Internal domains
                ]
                
                for pattern in suspicious_patterns:
                    if re.match(pattern, hostname, re.IGNORECASE):
                        return False, "Access to internal resources is not allowed"
    
    return True, None


def validate_file_upload(file_storage, config: dict) -> tuple[bool, Optional[str]]:
    """
    Validate uploaded file for security.
    
    Args:
        file_storage: FileStorage object from Flask
        config: Security configuration dictionary
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not file_storage or not file_storage.filename:
        return False, "No file provided"
    
    upload_config = config.get('security', {}).get('upload_safety', {})
    
    # Check file size
    file_storage.seek(0, 2)  # Seek to end
    file_size = file_storage.tell()
    file_storage.seek(0)  # Reset to beginning
    
    max_size_mb = upload_config.get('max_file_size_mb', 10)
    max_size_bytes = max_size_mb * 1024 * 1024
    
    if file_size > max_size_bytes:
        return False, f"File size exceeds maximum of {max_size_mb}MB"
    
    # Check MIME type
    content_type = file_storage.content_type
    allowed_types = upload_config.get('allowed_mime_types', [
        'image/jpeg', 'image/jpg', 'image/png', 'image/webp'
    ])
    
    if content_type not in allowed_types:
        return False, f"File type '{content_type}' is not allowed"
    
    # Check filename for suspicious patterns
    filename = file_storage.filename
    suspicious_extensions = [
        '.exe', '.bat', '.cmd', '.sh', '.ps1', '.php', '.jsp', '.asp',
        '.js', '.jar', '.war', '.py', '.rb', '.pl', '.cgi'
    ]
    
    filename_lower = filename.lower()
    for ext in suspicious_extensions:
        if filename_lower.endswith(ext):
            return False, f"Executable files are not allowed"
    
    # Check for path traversal attempts
    if '..' in filename or '/' in filename or '\\' in filename:
        return False, "Invalid filename: path traversal detected"
    
    return True, None


def add_security_headers(response, config: dict):
    """
    Add security headers to response.
    
    Args:
        response: Flask response object
        config: Security configuration dictionary
    
    Returns:
        Modified response object
    """
    headers_config = config.get('security', {}).get('headers', {})
    
    # X-Frame-Options
    if 'x_frame_options' in headers_config:
        response.headers['X-Frame-Options'] = headers_config['x_frame_options']
    
    # X-Content-Type-Options
    if 'x_content_type_options' in headers_config:
        response.headers['X-Content-Type-Options'] = headers_config['x_content_type_options']
    
    # X-XSS-Protection
    if 'x_xss_protection' in headers_config:
        response.headers['X-XSS-Protection'] = headers_config['x_xss_protection']
    
    # Strict-Transport-Security
    if 'strict_transport_security' in headers_config:
        response.headers['Strict-Transport-Security'] = headers_config['strict_transport_security']
    
    # Content-Security-Policy (optional, can be added later)
    # response.headers['Content-Security-Policy'] = "default-src 'self'"
    
    return response


def require_valid_request(config: dict):
    """
    Decorator to validate request before processing.
    
    Args:
        config: Security configuration dictionary
    
    Returns:
        Decorator function
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args: Any, **kwargs: Any) -> Any:
            # Check Content-Length for POST/PUT requests
            if request.method in ['POST', 'PUT']:
                content_length = request.content_length
                if content_length:
                    upload_config = config.get('security', {}).get('upload_safety', {})
                    max_size = upload_config.get('max_file_size_mb', 10) * 1024 * 1024
                    
                    if content_length > max_size * 2:  # Allow some overhead
                        return jsonify({
                            'error': 'Request too large',
                            'message': f'Maximum request size is {max_size // (1024 * 1024)}MB'
                        }), 413
            
            # Check Content-Type for JSON endpoints
            if request.path.startswith('/api/') and request.method == 'POST':
                if 'multipart/form-data' not in request.content_type and \
                   'application/json' not in request.content_type:
                    # Allow form-data for uploads, json for other endpoints
                    pass  # Some endpoints might not need JSON
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def init_security_middleware(app, config: dict):
    """
    Initialize all security middleware.
    
    Args:
        app: Flask application instance
        config: Security configuration dictionary
    """
    # Add security headers to all responses
    @app.after_request
    def apply_security_headers(response):
        return add_security_headers(response, config)
    
    # Log security events
    @app.before_request
    def log_request():
        logger.debug(
            f"Request: {request.method} {request.path} "
            f"from {get_remote_address()}"
        )
    
    logger.info("Security middleware initialized")
