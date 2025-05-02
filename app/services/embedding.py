import time
from typing import List, Optional

import torch
from sentence_transformers import SentenceTransformer  # type: ignore

# Load embedding models
E5_MODEL_NAME = "intfloat/multilingual-e5-base"
SBERT_MODEL_NAME = "sonoisa/sentence-bert-base-ja-mean-tokens-v2"
# Unload model after this many seconds of inactivity
MODEL_UNLOAD_TIMEOUT = 300  # 5 minutes


class EmbeddingService:
    """
    Service for text embedding using different models

    Lazy loads models only when needed and unloads them after a period of inactivity
    """

    def __init__(self):
        # Initialize models as None (lazy loading)
        self.e5_model: Optional[SentenceTransformer] = None
        self.sbert_model: Optional[SentenceTransformer] = None

        # Track last usage time for unloading
        self.e5_last_used: Optional[float] = None
        self.sbert_last_used: Optional[float] = None

        # Device for models
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

    def _load_e5_model(self) -> None:
        """
        Load the E5 model if not already loaded
        """
        if self.e5_model is None:
            print(f"Loading E5 embedding model on {self.device}...")
            self.e5_model = SentenceTransformer(E5_MODEL_NAME, device=self.device)
            print("E5 embedding model loaded successfully")

        # Update last used time
        self.e5_last_used = time.time()

    def _load_sbert_model(self) -> None:
        """
        Load the SBERT model if not already loaded
        """
        if self.sbert_model is None:
            print(f"Loading SBERT embedding model on {self.device}...")
            self.sbert_model = SentenceTransformer(SBERT_MODEL_NAME, device=self.device)
            print("SBERT embedding model loaded successfully")

        # Update last used time
        self.sbert_last_used = time.time()

    def _unload_models_if_inactive(self) -> None:
        """
        Unload models if they haven't been used for a while and are on GPU
        """
        current_time = time.time()

        # Check E5 model
        if (
            self.e5_model is not None
            and self.device == "cuda"
            and self.e5_last_used is not None
            and (current_time - self.e5_last_used) > MODEL_UNLOAD_TIMEOUT
        ):
            print("Unloading E5 embedding model from GPU due to inactivity")
            self.e5_model = None
            self.e5_last_used = None

        # Check SBERT model
        if (
            self.sbert_model is not None
            and self.device == "cuda"
            and self.sbert_last_used is not None
            and (current_time - self.sbert_last_used) > MODEL_UNLOAD_TIMEOUT
        ):
            print("Unloading SBERT embedding model from GPU due to inactivity")
            self.sbert_model = None
            self.sbert_last_used = None

        # Force garbage collection to free GPU memory if any model was unloaded
        if (
            self.e5_model is None or self.sbert_model is None
        ) and torch.cuda.is_available():
            torch.cuda.empty_cache()

    def get_e5_embedding(self, text: str) -> List[float]:
        """
        Get embedding using multilingual-e5-base model

        Loads the model if not already loaded
        """
        # Check if models should be unloaded due to inactivity
        self._unload_models_if_inactive()

        # Load model if not loaded
        self._load_e5_model()

        # Format text for e5 model
        formatted_text = f"query: {text}"

        # Get embedding
        embedding = self.e5_model.encode(formatted_text, normalize_embeddings=True)  # type: ignore

        # Update last used time
        self.e5_last_used = time.time()

        return embedding.tolist()

    def get_sbert_embedding(self, text: str) -> List[float]:
        """
        Get embedding using sentence-bert-base-ja-mean-tokens-v2 model

        Loads the model if not already loaded
        """
        # Check if models should be unloaded due to inactivity
        self._unload_models_if_inactive()

        # Load model if not loaded
        self._load_sbert_model()

        # Get embedding
        embedding = self.sbert_model.encode(text, normalize_embeddings=True)  # type: ignore

        # Update last used time
        self.sbert_last_used = time.time()

        return embedding.tolist()


# Singleton instance
embedding_service = EmbeddingService()
