"""
Tests for ImageService.
"""
import pytest
import os
from PIL import Image


def test_validate_extension(image_service):
    """Test file extension validation."""
    assert image_service.validate_extension('test.jpg') is True
    assert image_service.validate_extension('test.jpeg') is True
    assert image_service.validate_extension('test.png') is True
    assert image_service.validate_extension('test.webp') is True
    assert image_service.validate_extension('test.txt') is False
    assert image_service.validate_extension('test') is False


def test_validate_image_file_valid(image_service, create_test_image):
    """Test validation of valid image file."""
    image_path = create_test_image()
    
    try:
        is_valid, error = image_service.validate_image_file(image_path)
        assert is_valid is True
        assert error is None
    finally:
        if os.path.exists(image_path):
            os.remove(image_path)


def test_validate_image_file_not_exists(image_service):
    """Test validation of non-existent file."""
    is_valid, error = image_service.validate_image_file('/nonexistent/file.jpg')
    assert is_valid is False
    assert 'not exist' in error.lower()


def test_validate_image_file_too_large(image_service, create_test_image):
    """Test validation of oversized file."""
    image_path = create_test_image(width=5000, height=5000)
    
    try:
        # Mock smaller max size
        original_max_size = image_service.max_file_size
        image_service.max_file_size = 1000  # 1000 bytes
        
        is_valid, error = image_service.validate_image_file(image_path)
        assert is_valid is False
        assert 'exceeds' in error.lower()
        
        # Restore
        image_service.max_file_size = original_max_size
    finally:
        if os.path.exists(image_path):
            os.remove(image_path)


def test_get_image_metadata(image_service, create_test_image):
    """Test extracting image metadata."""
    image_path = create_test_image(width=200, height=150)
    
    try:
        metadata = image_service.get_image_metadata(image_path)
        
        assert metadata['width'] == 200
        assert metadata['height'] == 150
        assert metadata['format'] in ['JPEG', 'PNG']
        assert metadata['file_size'] > 0
    finally:
        if os.path.exists(image_path):
            os.remove(image_path)


def test_resize_image(image_service, create_test_image):
    """Test image resizing."""
    image_path = create_test_image(width=500, height=400)
    
    try:
        resized = image_service.resize_image(image_path, max_size=(224, 224))
        
        assert resized.width <= 224
        assert resized.height <= 224
    finally:
        if os.path.exists(image_path):
            os.remove(image_path)


def test_generate_safe_filename(image_service):
    """Test safe filename generation."""
    filename = image_service._generate_safe_filename('test image.jpg')
    
    assert '.jpg' in filename
    assert 'test' in filename.lower()
    assert ' ' not in filename  # Spaces should be removed/replaced
