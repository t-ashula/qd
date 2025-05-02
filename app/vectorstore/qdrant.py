import os
import uuid
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, PointStruct, ScoredPoint, VectorParams

# Load environment variables
load_dotenv()

# Qdrant connection settings
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = os.getenv("QDRANT_PORT", "6333")

# Collection names
COLLECTION_E5 = "episodes_e5"
COLLECTION_V2 = "episodes_v2"

# Vector dimensions
VECTOR_DIM = 768


class QdrantManager:
    """
    Manager for Qdrant vector database operations
    """

    def __init__(self):
        self.client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

    def init_collections(self):
        """
        Initialize Qdrant collections if they don't exist
        """
        # Check if collections exist
        collections = self.client.get_collections().collections
        collection_names = [collection.name for collection in collections]

        # Create E5 collection if it doesn't exist
        if COLLECTION_E5 not in collection_names:
            self.client.create_collection(
                collection_name=COLLECTION_E5,
                vectors_config=VectorParams(size=VECTOR_DIM, distance=Distance.COSINE),
            )

        # Create V2 collection if it doesn't exist
        if COLLECTION_V2 not in collection_names:
            self.client.create_collection(
                collection_name=COLLECTION_V2,
                vectors_config=VectorParams(size=VECTOR_DIM, distance=Distance.COSINE),
            )

    def add_segment_e5(self, vector: List[float], payload: Dict[str, Any]):
        """
        Add a segment to the E5 collection
        """
        self.client.upsert(
            collection_name=COLLECTION_E5,
            points=[
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vector,
                    payload=payload,
                )
            ],
        )

    def add_segment_v2(self, vector: List[float], payload: Dict[str, Any]):
        """
        Add a segment to the V2 collection
        """
        self.client.upsert(
            collection_name=COLLECTION_V2,
            points=[
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vector,
                    payload=payload,
                )
            ],
        )

    def search_e5(self, vector: List[float], limit: int = 10):
        """
        Search the E5 collection
        """
        return self.client.search(
            collection_name=COLLECTION_E5,
            query_vector=vector,
            limit=limit,
        )

    def search_v2(self, vector: List[float], limit: int = 10):
        """
        Search the V2 collection
        """
        return self.client.search(
            collection_name=COLLECTION_V2,
            query_vector=vector,
            limit=limit,
        )


# Singleton instance
qdrant_manager = QdrantManager()
