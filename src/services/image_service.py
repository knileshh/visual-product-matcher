"""
Image service for handling image upload, validation, and processing.
"""
import os
import logging
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image
import requests
from io import BytesIO

logger = logging.getLogger(__name__)


class ImageService:
    """Service for image validation, upload, and processing."""
    
    def __init__(self, config: dict):
        """
        Initialize image service.
        
        Args:
            config: Configuration dictionary with upload settings
        """
        self.config = config
        self.upload_folder = config['upload']['upload_folder']
        self.temp_folder = config['upload']['temp_folder']
        self.max_file_size = config['upload']['max_file_size_mb'] * 1024 * 1024  # Convert to bytes
        self.allowed_extensions = set(config['upload']['allowed_extensions'])
        
        # Create directories if they don't exist
        Path(self.upload_folder).mkdir(parents=True, exist_ok=True)
        Path(self.temp_folder).mkdir(parents=True, exist_ok=True)
    
    def validate_extension(self, filename: str) -> bool:
        """
        Validate file extension.
        
        Args:
            filename: Name of file to validate
            
        Returns:
            True if extension is allowed, False otherwise
        """
        if '.' not in filename:
            return False
        
        extension = filename.rsplit('.', 1)[1].lower()
        return extension in self.allowed_extensions
    
    def validate_image_file(self, image_path: str) -> Tuple[bool, Optional[str]]:
        """
        Validate image file format and integrity.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check file exists
            if not os.path.exists(image_path):
                return False, "File does not exist"
            
            # Check file size
            file_size = os.path.getsize(image_path)
            if file_size > self.max_file_size:
                max_mb = self.max_file_size / (1024 * 1024)
                return False, f"File size exceeds maximum allowed size of {max_mb}MB"
            
            if file_size == 0:
                return False, "File is empty"
            
            # Try to open and verify image
            with Image.open(image_path) as img:
                img.verify()
            
            # Open again to check format (verify() closes the file)
            with Image.open(image_path) as img:
                if img.format.lower() not in ['jpeg', 'jpg', 'png', 'webp']:
                    return False, f"Unsupported image format: {img.format}"
            
            return True, None
            
        except Exception as e:
            logger.error(f"Error validating image: {str(e)}")
            return False, f"Invalid image file: {str(e)}"
    
    def download_image_from_url(self, url: str, save_path: str) -> Tuple[bool, Optional[str]]:
        """
        Download image from URL.
        
        Args:
            url: URL to download image from
            save_path: Path to save downloaded image
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Validate URL format
            if not url.startswith(('http://', 'https://')):
                return False, "Invalid URL format"
            
            # Download with timeout
            response = requests.get(url, timeout=10, stream=True)
            response.raise_for_status()
            
            # Check content type
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                return False, f"URL does not point to an image (content-type: {content_type})"
            
            # Check size before downloading fully
            content_length = response.headers.get('content-length')
            if content_length and int(content_length) > self.max_file_size:
                max_mb = self.max_file_size / (1024 * 1024)
                return False, f"Image size exceeds maximum allowed size of {max_mb}MB"
            
            # Save image
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Validate downloaded image
            is_valid, error = self.validate_image_file(save_path)
            if not is_valid:
                # Clean up invalid file
                if os.path.exists(save_path):
                    os.remove(save_path)
                return False, error
            
            logger.info(f"Successfully downloaded image from URL to {save_path}")
            return True, None
            
        except requests.exceptions.Timeout:
            return False, "Request timeout - URL took too long to respond"
        except requests.exceptions.RequestException as e:
            return False, f"Failed to download image: {str(e)}"
        except Exception as e:
            logger.error(f"Error downloading image: {str(e)}")
            return False, f"Error downloading image: {str(e)}"
    
    def process_uploaded_file(self, file_storage, filename: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Process uploaded file from Flask request.
        
        Args:
            file_storage: FileStorage object from Flask
            filename: Desired filename
            
        Returns:
            Tuple of (success, error_message, saved_path)
        """
        try:
            # Validate filename extension
            if not self.validate_extension(filename):
                return False, "Invalid file extension", None
            
            # Generate safe filename
            safe_filename = self._generate_safe_filename(filename)
            save_path = os.path.join(self.upload_folder, safe_filename)
            
            # Save file
            file_storage.save(save_path)
            
            # Validate saved image
            is_valid, error = self.validate_image_file(save_path)
            if not is_valid:
                # Clean up invalid file
                if os.path.exists(save_path):
                    os.remove(save_path)
                return False, error, None
            
            logger.info(f"Successfully processed uploaded file: {safe_filename}")
            return True, None, save_path
            
        except Exception as e:
            logger.error(f"Error processing uploaded file: {str(e)}")
            return False, f"Error processing file: {str(e)}", None
    
    def resize_image(self, image_path: str, max_size: Tuple[int, int] = (224, 224)) -> Image.Image:
        """
        Resize image maintaining aspect ratio.
        
        Args:
            image_path: Path to image file
            max_size: Maximum size (width, height)
            
        Returns:
            Resized PIL Image object
        """
        with Image.open(image_path) as img:
            # Convert RGBA to RGB if necessary
            if img.mode == 'RGBA':
                img = img.convert('RGB')
            
            # Resize maintaining aspect ratio
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            return img.copy()
    
    def get_image_metadata(self, image_path: str) -> dict:
        """
        Extract metadata from image file.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Dictionary with image metadata
        """
        try:
            with Image.open(image_path) as img:
                metadata = {
                    'width': img.width,
                    'height': img.height,
                    'format': img.format,
                    'mode': img.mode,
                    'file_size': os.path.getsize(image_path)
                }
                return metadata
        except Exception as e:
            logger.error(f"Error extracting image metadata: {str(e)}")
            return {}
    
    def _generate_safe_filename(self, filename: str) -> str:
        """
        Generate safe filename with timestamp.
        
        Args:
            filename: Original filename
            
        Returns:
            Safe filename with timestamp
        """
        import time
        name, ext = os.path.splitext(filename)
        # Remove potentially dangerous characters
        safe_name = "".join(c for c in name if c.isalnum() or c in ('-', '_'))
        timestamp = int(time.time())
        return f"{safe_name}_{timestamp}{ext}"
    
    def cleanup_temp_files(self) -> None:
        """Remove all temporary files."""
        try:
            temp_path = Path(self.temp_folder)
            for file in temp_path.glob('*'):
                if file.is_file():
                    file.unlink()
            logger.info("Cleaned up temporary files")
        except Exception as e:
            logger.error(f"Error cleaning up temp files: {str(e)}")
