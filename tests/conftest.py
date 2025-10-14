"""
Pytest configuration and fixtures for Visual Product Matcher tests.
"""
import pytest
import tempfile
import os
from pathlib import Path
import numpy as np
from PIL import Image
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models import Database, Product
from src.services.image_service import ImageService
from src.services.embedding_service import EmbeddingService
from src.services.search_service import SearchService


@pytest.fixture
def test_config():
    """Test configuration."""
    return {
        'app': {
            'name': 'Test App',
            'debug': True,
            'secret_key': 'test-secret-key'
        },
        'upload': {
            'max_file_size_mb': 5,
            'allowed_extensions': ['jpg', 'jpeg', 'png', 'webp'],
            'upload_folder': tempfile.mkdtemp(),
            'temp_folder': tempfile.mkdtemp()
        },
        'ml': {
            'clip_model': 'ViT-B/32',
            'device': 'cpu',
            'embedding_dimension': 512,
            'batch_size': 4
        },
        'search': {
            'default_k': 10,
            'min_similarity_threshold': 0.0,
            'max_similarity_threshold': 1.0,
            'default_similarity_threshold': 0.3
        },
        'database': {
            'type': 'sqlite',
            'path': ':memory:',  # In-memory database for tests
            'echo': False
        },
        'index': {
            'faiss_index_path': os.path.join(tempfile.mkdtemp(), 'test.index'),
            'embeddings_cache_path': os.path.join(tempfile.mkdtemp(), 'test_embeddings.npy'),
            'metadata_cache_path': os.path.join(tempfile.mkdtemp(), 'test_metadata.json'),
            'rebuild_on_startup': False
        },
        'products': {
            'images_directory': 'fashion-images',
            'supported_formats': ['jpg', 'jpeg', 'png', 'webp']
        }
    }


@pytest.fixture
def temp_db():
    """Temporary in-memory database."""
    db = Database(':memory:')
    yield db
    # Cleanup happens automatically with in-memory database


@pytest.fixture
def sample_product():
    """Sample product for testing."""
    return Product(
        id=1,
        name='Test Product',
        image_path='/path/to/image.jpg',
        category='Fashion',
        file_size=1024,
        width=500,
        height=500,
        format='JPEG'
    )


@pytest.fixture
def create_test_image():
    """Factory fixture to create test images."""
    def _create_image(width=100, height=100, color=(255, 0, 0)):
        """Create a test image."""
        img = Image.new('RGB', (width, height), color=color)
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
        img.save(temp_file.name, 'JPEG')
        temp_file.close()
        return temp_file.name
    
    yield _create_image


@pytest.fixture
def sample_embedding():
    """Sample embedding vector for testing."""
    # Create a normalized random embedding
    embedding = np.random.randn(512).astype('float32')
    embedding = embedding / np.linalg.norm(embedding)
    return embedding


@pytest.fixture
def mock_embeddings():
    """Mock embeddings for multiple products."""
    # Create 10 normalized random embeddings
    embeddings = np.random.randn(10, 512).astype('float32')
    for i in range(len(embeddings)):
        embeddings[i] = embeddings[i] / np.linalg.norm(embeddings[i])
    return embeddings


@pytest.fixture
def image_service(test_config):
    """ImageService instance for testing."""
    return ImageService(test_config)


@pytest.fixture
def search_service(test_config):
    """SearchService instance for testing."""
    return SearchService(test_config)


# Mock for EmbeddingService to avoid loading CLIP in tests
class MockEmbeddingService:
    """Mock embedding service for testing."""
    
    def __init__(self, config):
        self.config = config
        self.embedding_dim = config['ml']['embedding_dimension']
    
    def generate_embedding(self, image_path):
        """Generate mock embedding."""
        embedding = np.random.randn(self.embedding_dim).astype('float32')
        embedding = embedding / np.linalg.norm(embedding)
        return embedding
    
    def generate_embeddings_batch(self, image_paths):
        """Generate mock embeddings batch."""
        embeddings = []
        for _ in image_paths:
            embedding = self.generate_embedding(None)
            embeddings.append(embedding)
        return np.array(embeddings)
    
    def get_device_info(self):
        """Get mock device info."""
        return {
            'device': 'cpu',
            'model': 'ViT-B/32',
            'embedding_dimension': self.embedding_dim
        }


@pytest.fixture
def mock_embedding_service(test_config):
    """Mock EmbeddingService for testing without loading CLIP."""
    return MockEmbeddingService(test_config)
