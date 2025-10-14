"""
Tests for SearchService.
"""
import pytest
import numpy as np


def test_build_index(search_service, mock_embeddings):
    """Test building FAISS index."""
    product_ids = list(range(1, 11))
    
    search_service.build_index(mock_embeddings, product_ids)
    
    assert search_service.index is not None
    assert len(search_service.product_ids) == 10


def test_build_index_empty_embeddings(search_service):
    """Test building index with empty embeddings."""
    with pytest.raises(ValueError, match="empty"):
        search_service.build_index(np.array([]), [])


def test_build_index_mismatched_lengths(search_service, mock_embeddings):
    """Test building index with mismatched lengths."""
    product_ids = [1, 2, 3]  # Only 3 IDs for 10 embeddings
    
    with pytest.raises(ValueError, match="must match"):
        search_service.build_index(mock_embeddings, product_ids)


def test_search(search_service, mock_embeddings, sample_embedding):
    """Test similarity search."""
    product_ids = list(range(1, 11))
    search_service.build_index(mock_embeddings, product_ids)
    
    results = search_service.search(sample_embedding, k=5)
    
    assert len(results) <= 5
    assert all(isinstance(r[0], int) for r in results)  # Product IDs
    assert all(isinstance(r[1], float) for r in results)  # Similarity scores
    assert all(0 <= r[1] <= 1 for r in results)  # Scores in valid range


def test_search_with_threshold(search_service, mock_embeddings, sample_embedding):
    """Test search with similarity threshold."""
    product_ids = list(range(1, 11))
    search_service.build_index(mock_embeddings, product_ids)
    
    results = search_service.search(sample_embedding, k=10, similarity_threshold=0.8)
    
    # All results should meet threshold
    assert all(r[1] >= 0.8 for r in results)


def test_search_no_index(search_service, sample_embedding):
    """Test search without loading index."""
    with pytest.raises(ValueError, match="not loaded"):
        search_service.search(sample_embedding)


def test_get_index_stats_loaded(search_service, mock_embeddings):
    """Test getting index stats when loaded."""
    product_ids = list(range(1, 11))
    search_service.build_index(mock_embeddings, product_ids)
    
    stats = search_service.get_index_stats()
    
    assert stats['status'] == 'loaded'
    assert stats['num_products'] == 10
    assert stats['embedding_dimension'] == 512


def test_get_index_stats_not_loaded(search_service):
    """Test getting index stats when not loaded."""
    stats = search_service.get_index_stats()
    
    assert stats['status'] == 'not_loaded'


def test_save_and_load_index(search_service, mock_embeddings, tmp_path):
    """Test saving and loading index."""
    # Update paths to use temp directory
    search_service.index_path = str(tmp_path / 'test.index')
    search_service.embeddings_cache = str(tmp_path / 'embeddings.npy')
    search_service.metadata_cache = str(tmp_path / 'metadata.json')
    
    product_ids = list(range(1, 11))
    search_service.build_index(mock_embeddings, product_ids)
    
    # Save index
    search_service.save_index()
    
    # Create new service instance and load
    new_service = SearchService(search_service.config)
    new_service.index_path = search_service.index_path
    new_service.embeddings_cache = search_service.embeddings_cache
    new_service.metadata_cache = search_service.metadata_cache
    
    loaded = new_service.load_index()
    
    assert loaded is True
    assert len(new_service.product_ids) == 10
    assert new_service.index is not None
