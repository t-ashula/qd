from typing import List

import torch
from sentence_transformers import SentenceTransformer  # type: ignore

# Load embedding models
E5_MODEL_NAME = "intfloat/multilingual-e5-base"
SBERT_MODEL_NAME = "sonoisa/sentence-bert-base-ja-mean-tokens-v2"


class EmbeddingService:
    """
    Service for text embedding using different models
    """

    def __init__(self):
        # Load models
        self.e5_model = SentenceTransformer(E5_MODEL_NAME)
        self.sbert_model = SentenceTransformer(SBERT_MODEL_NAME)

    def get_e5_embedding(self, text: str) -> List[float]:
        """
        Get embedding using multilingual-e5-base model
        """
        # Format text for e5 model
        formatted_text = f"query: {text}"
        # Get embedding
        embedding = self.e5_model.encode(formatted_text, normalize_embeddings=True)
        return embedding.tolist()

    def get_sbert_embedding(self, text: str) -> List[float]:
        """
        Get embedding using sentence-bert-base-ja-mean-tokens-v2 model
        """
        # Get embedding
        embedding = self.sbert_model.encode(text, normalize_embeddings=True)
        return embedding.tolist()


# Singleton instance
embedding_service = EmbeddingService()
