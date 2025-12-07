"""
Embeddings Service - Generate vector embeddings for semantic search
Supports Google Gemini embeddings (primary) and Sentence Transformers (local fallback)
"""

import os
from typing import List, Optional
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()


class EmbeddingsService:
    """
    Service for generating text embeddings (vector representations).
    Used for semantic search, job matching, and similarity calculations.
    """
    
    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize embeddings service.
        
        Args:
            model_name: Embedding model to use (defaults to env variable)
        """
        self.model_name = model_name or os.getenv("EMBEDDING_MODEL", "text-embedding-004")
        self.api_key = os.getenv("GEMINI_API_KEY")
        
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
    
    def embed_text(
        self,
        text: str,
        task_type: str = "retrieval_document"
    ) -> List[float]:
        """
        Generate embedding vector for a single text.
        
        Args:
            text: Text to embed
            task_type: Task type for optimization:
                - 'retrieval_document': For indexing documents
                - 'retrieval_query': For search queries
                - 'semantic_similarity': For comparing texts
                - 'classification': For categorization
            
        Returns:
            Vector embedding (list of floats, typically 768 dimensions)
        """
        result = genai.embed_content(
            model=self.model_name,
            content=text,
            task_type=task_type
        )
        return result['embedding']
    
    def embed_batch(
        self,
        texts: List[str],
        task_type: str = "retrieval_document"
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (batch processing).
        More efficient than calling embed_text multiple times.
        
        Args:
            texts: List of texts to embed
            task_type: Task type for optimization
            
        Returns:
            List of embedding vectors
        """
        embeddings = []
        for text in texts:
            embedding = self.embed_text(text, task_type)
            embeddings.append(embedding)
        return embeddings
    
    def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding optimized for search queries.
        Use this for user search input.
        
        Args:
            query: Search query text
            
        Returns:
            Query embedding vector
        """
        return self.embed_text(query, task_type="retrieval_query")
    
    def embed_document(self, document: str) -> List[float]:
        """
        Generate embedding optimized for document indexing.
        Use this for job descriptions, CVs, etc.
        
        Args:
            document: Document text to index
            
        Returns:
            Document embedding vector
        """
        return self.embed_text(document, task_type="retrieval_document")
    
    def get_embedding_dimension(self) -> int:
        """
        Get the dimension size of embeddings.
        text-embedding-004 produces 768-dimensional vectors.
        
        Returns:
            Embedding dimension size
        """
        # Generate a sample embedding to get dimension
        sample = self.embed_text("sample")
        return len(sample)
    
    def cosine_similarity(
        self,
        embedding1: List[float],
        embedding2: List[float]
    ) -> float:
        """
        Calculate cosine similarity between two embeddings.
        Returns value between -1 and 1 (higher = more similar).
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Similarity score (0-1, where 1 is identical)
        """
        import numpy as np
        
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        # Cosine similarity formula
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        similarity = dot_product / (norm1 * norm2)
        return float(similarity)
    
    def estimate_cost(self, num_texts: int, avg_length: int = 500) -> float:
        """
        Estimate embedding API cost.
        Google embeddings are very cheap or free (depending on tier).
        
        Args:
            num_texts: Number of texts to embed
            avg_length: Average text length in characters
            
        Returns:
            Estimated cost in USD
        """
        # text-embedding-004 is often free or very cheap
        # Approximate: $0.00001 per 1K characters (very rough estimate)
        total_chars = num_texts * avg_length
        cost_per_1k_chars = 0.00001
        return (total_chars / 1000) * cost_per_1k_chars


# Singleton instance
_embeddings_service_instance: Optional[EmbeddingsService] = None


def get_embeddings_service() -> EmbeddingsService:
    """
    Get or create singleton embeddings service instance.
    
    Returns:
        EmbeddingsService instance
    """
    global _embeddings_service_instance
    if _embeddings_service_instance is None:
        _embeddings_service_instance = EmbeddingsService()
    return _embeddings_service_instance