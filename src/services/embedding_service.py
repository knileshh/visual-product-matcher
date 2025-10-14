"""
Embedding service using CLIP for semantic image understanding.
"""
import logging
import torch
import numpy as np
from PIL import Image
from typing import List, Optional, Union
import clip

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating image embeddings using CLIP."""
    
    def __init__(self, config: dict):
        """
        Initialize CLIP model for embedding generation.
        
        Args:
            config: Configuration dictionary with ML settings
        """
        self.config = config
        self.model_name = config['ml']['clip_model']
        self.device_config = config['ml']['device']
        self.embedding_dim = config['ml']['embedding_dimension']
        self.batch_size = config['ml']['batch_size']
        
        # Setup device
        self.device = self._setup_device()
        
        # Load CLIP model
        self.model, self.preprocess = self._load_model()
        
        logger.info(f"Embedding service initialized with {self.model_name} on {self.device}")
    
    def _setup_device(self) -> torch.device:
        """
        Setup computation device (CUDA or CPU).
        
        Returns:
            torch.device object
        """
        if self.device_config == "cuda" and torch.cuda.is_available():
            device = torch.device("cuda")
            logger.info(f"Using CUDA GPU: {torch.cuda.get_device_name(0)}")
        else:
            device = torch.device("cpu")
            if self.device_config == "cuda":
                logger.warning("CUDA requested but not available, falling back to CPU")
            else:
                logger.info("Using CPU for inference")
        
        return device
    
    def _load_model(self):
        """
        Load CLIP model and preprocessing pipeline.
        
        Returns:
            Tuple of (model, preprocess)
        """
        try:
            model, preprocess = clip.load(self.model_name, device=self.device)
            model.eval()  # Set to evaluation mode
            logger.info(f"Successfully loaded CLIP model: {self.model_name}")
            return model, preprocess
        except Exception as e:
            logger.error(f"Failed to load CLIP model: {str(e)}")
            raise
    
    def generate_embedding(self, image_path: str) -> Optional[np.ndarray]:
        """
        Generate embedding for a single image.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Numpy array of embedding vector or None on error
        """
        try:
            # Load and preprocess image
            image = Image.open(image_path)
            
            # Convert RGBA to RGB if necessary
            if image.mode == 'RGBA':
                image = image.convert('RGB')
            
            image_input = self.preprocess(image).unsqueeze(0).to(self.device)
            
            # Generate embedding
            with torch.no_grad():
                image_features = self.model.encode_image(image_input)
                # Normalize embedding
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            
            # Convert to numpy array
            embedding = image_features.cpu().numpy().flatten()
            
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding for {image_path}: {str(e)}")
            return None
    
    def generate_embeddings_batch(self, image_paths: List[str]) -> np.ndarray:
        """
        Generate embeddings for multiple images in batches.
        
        Args:
            image_paths: List of paths to image files
            
        Returns:
            Numpy array of shape (n_images, embedding_dim)
        """
        embeddings = []
        
        # Process in batches
        for i in range(0, len(image_paths), self.batch_size):
            batch_paths = image_paths[i:i + self.batch_size]
            batch_embeddings = self._process_batch(batch_paths)
            embeddings.extend(batch_embeddings)
            
            # Log progress
            if (i + self.batch_size) % 100 == 0 or (i + self.batch_size) >= len(image_paths):
                logger.info(f"Processed {min(i + self.batch_size, len(image_paths))}/{len(image_paths)} images")
        
        return np.array(embeddings)
    
    def _process_batch(self, image_paths: List[str]) -> List[np.ndarray]:
        """
        Process a batch of images.
        
        Args:
            image_paths: List of image paths for the batch
            
        Returns:
            List of embedding arrays
        """
        batch_embeddings = []
        images = []
        valid_indices = []
        
        # Load and preprocess all images in batch
        for idx, path in enumerate(image_paths):
            try:
                image = Image.open(path)
                if image.mode == 'RGBA':
                    image = image.convert('RGB')
                images.append(self.preprocess(image))
                valid_indices.append(idx)
            except Exception as e:
                logger.error(f"Error loading image {path}: {str(e)}")
                # Add zero embedding for failed images
                batch_embeddings.append(np.zeros(self.embedding_dim))
        
        if not images:
            return batch_embeddings
        
        try:
            # Stack images into batch tensor
            image_batch = torch.stack(images).to(self.device)
            
            # Generate embeddings
            with torch.no_grad():
                features = self.model.encode_image(image_batch)
                # Normalize embeddings
                features = features / features.norm(dim=-1, keepdim=True)
            
            # Convert to numpy
            features_np = features.cpu().numpy()
            
            # Insert embeddings at correct positions
            feature_idx = 0
            for idx in range(len(image_paths)):
                if idx in valid_indices:
                    batch_embeddings.insert(idx, features_np[feature_idx])
                    feature_idx += 1
            
        except Exception as e:
            logger.error(f"Error processing batch: {str(e)}")
            # Return zero embeddings for failed batch
            batch_embeddings = [np.zeros(self.embedding_dim) for _ in image_paths]
        
        return batch_embeddings
    
    def compute_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Compute cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity score (0-1)
        """
        # Embeddings are already normalized by CLIP, so dot product = cosine similarity
        similarity = np.dot(embedding1, embedding2)
        # Ensure similarity is in [0, 1] range
        similarity = (similarity + 1) / 2  # Convert from [-1, 1] to [0, 1]
        return float(similarity)
    
    def get_device_info(self) -> dict:
        """
        Get information about the computation device.
        
        Returns:
            Dictionary with device information
        """
        info = {
            'device': str(self.device),
            'model': self.model_name,
            'embedding_dimension': self.embedding_dim
        }
        
        if self.device.type == 'cuda':
            info.update({
                'gpu_name': torch.cuda.get_device_name(0),
                'gpu_memory_allocated': f"{torch.cuda.memory_allocated(0) / 1024**2:.2f} MB",
                'gpu_memory_cached': f"{torch.cuda.memory_reserved(0) / 1024**2:.2f} MB"
            })
        
        return info
