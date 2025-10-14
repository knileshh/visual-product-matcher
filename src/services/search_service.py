"""
Search service using FAISS for efficient similarity search.
"""
import logging
import numpy as np
import faiss
import json
from pathlib import Path
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)


class SearchService:
    """Service for FAISS-based similarity search."""
    
    def __init__(self, config: dict):
        """
        Initialize search service.
        
        Args:
            config: Configuration dictionary with index settings
        """
        self.config = config
        self.index_path = config['index']['faiss_index_path']
        self.embeddings_cache = config['index']['embeddings_cache_path']
        self.metadata_cache = config['index']['metadata_cache_path']
        self.embedding_dim = config['ml']['embedding_dimension']
        self.default_k = config['search']['default_k']
        
        self.index: Optional[faiss.Index] = None
        self.product_ids: List[int] = []
        self.embeddings: Optional[np.ndarray] = None
        
        # Ensure directories exist
        Path(self.index_path).parent.mkdir(parents=True, exist_ok=True)
        Path(self.embeddings_cache).parent.mkdir(parents=True, exist_ok=True)
        
        logger.info("Search service initialized")
    
    def build_index(self, embeddings: np.ndarray, product_ids: List[int]) -> None:
        """
        Build FAISS index from embeddings.
        
        Args:
            embeddings: Numpy array of shape (n_products, embedding_dim)
            product_ids: List of product IDs corresponding to embeddings
        """
        if len(embeddings) == 0:
            raise ValueError("Cannot build index with empty embeddings")
        
        if len(embeddings) != len(product_ids):
            raise ValueError(f"Embeddings count ({len(embeddings)}) must match product IDs count ({len(product_ids)})")
        
        # Normalize embeddings for cosine similarity
        embeddings = embeddings.astype('float32')
        faiss.normalize_L2(embeddings)
        
        # Create FAISS index
        # Using IndexFlatL2 for exact search (good for up to 1M vectors)
        # For larger datasets, consider IndexIVFFlat
        self.index = faiss.IndexFlatL2(self.embedding_dim)
        
        # Add embeddings to index
        self.index.add(embeddings)
        
        self.embeddings = embeddings
        self.product_ids = product_ids
        
        logger.info(f"Built FAISS index with {len(product_ids)} products")
    
    def save_index(self) -> None:
        """Save FAISS index and metadata to disk."""
        if self.index is None:
            raise ValueError("No index to save. Build index first.")
        
        try:
            # Save FAISS index
            faiss.write_index(self.index, self.index_path)
            logger.info(f"Saved FAISS index to {self.index_path}")
            
            # Save embeddings
            np.save(self.embeddings_cache, self.embeddings)
            logger.info(f"Saved embeddings to {self.embeddings_cache}")
            
            # Save metadata (product IDs)
            metadata = {
                'product_ids': self.product_ids,
                'embedding_dim': self.embedding_dim,
                'num_products': len(self.product_ids)
            }
            with open(self.metadata_cache, 'w') as f:
                json.dump(metadata, f)
            logger.info(f"Saved metadata to {self.metadata_cache}")
            
        except Exception as e:
            logger.error(f"Error saving index: {str(e)}")
            raise
    
    def load_index(self) -> bool:
        """
        Load FAISS index and metadata from disk.
        
        Returns:
            True if successfully loaded, False otherwise
        """
        try:
            # Check if files exist
            if not Path(self.index_path).exists():
                logger.warning(f"Index file not found: {self.index_path}")
                return False
            
            if not Path(self.metadata_cache).exists():
                logger.warning(f"Metadata file not found: {self.metadata_cache}")
                return False
            
            # Load FAISS index
            self.index = faiss.read_index(self.index_path)
            logger.info(f"Loaded FAISS index from {self.index_path}")
            
            # Load embeddings if available
            if Path(self.embeddings_cache).exists():
                self.embeddings = np.load(self.embeddings_cache)
                logger.info(f"Loaded embeddings from {self.embeddings_cache}")
            
            # Load metadata
            with open(self.metadata_cache, 'r') as f:
                metadata = json.load(f)
            
            self.product_ids = metadata['product_ids']
            logger.info(f"Loaded metadata with {len(self.product_ids)} products")
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading index: {str(e)}")
            return False
    
    def search(
        self,
        query_embedding: np.ndarray,
        k: Optional[int] = None,
        similarity_threshold: float = 0.0
    ) -> List[Tuple[int, float]]:
        """
        Search for similar products.
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return (default: from config)
            similarity_threshold: Minimum similarity score (0-1)
            
        Returns:
            List of tuples (product_id, similarity_score)
        """
        if self.index is None:
            raise ValueError("Index not loaded. Call load_index() or build_index() first.")
        
        k = k or self.default_k
        
        # Ensure query embedding is correct shape and type
        query_embedding = query_embedding.astype('float32').reshape(1, -1)
        
        # Normalize query embedding
        faiss.normalize_L2(query_embedding)
        
        # Search - get more results than k to filter by threshold
        search_k = min(k * 3, len(self.product_ids))
        distances, indices = self.index.search(query_embedding, search_k)
        
        # Convert L2 distances to cosine similarities
        # For normalized vectors: similarity = 1 - (L2_distance^2 / 2)
        similarities = 1 - (distances[0] ** 2) / 2
        
        # Filter and prepare results
        results = []
        for idx, similarity in zip(indices[0], similarities):
            if idx == -1:  # FAISS returns -1 for empty slots
                continue
            
            if similarity >= similarity_threshold:
                product_id = self.product_ids[idx]
                results.append((product_id, float(similarity)))
            
            if len(results) >= k:
                break
        
        logger.debug(f"Found {len(results)} similar products")
        return results
    
    def get_index_stats(self) -> dict:
        """
        Get statistics about the index.
        
        Returns:
            Dictionary with index statistics
        """
        if self.index is None:
            return {'status': 'not_loaded'}
        
        return {
            'status': 'loaded',
            'num_products': len(self.product_ids),
            'embedding_dimension': self.embedding_dim,
            'index_size': self.index.ntotal,
            'index_type': type(self.index).__name__
        }
    
    def index_exists(self) -> bool:
        """
        Check if index files exist on disk.
        
        Returns:
            True if index files exist, False otherwise
        """
        return (
            Path(self.index_path).exists() and
            Path(self.metadata_cache).exists()
        )
