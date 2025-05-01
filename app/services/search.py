import heapq
from typing import Any, Dict, List

from app.services.embedding import embedding_service
from app.vectorstore.qdrant import qdrant_manager


class SearchService:
    """
    Service for searching episodes using vector search
    """

    def search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search episodes using vector search

        Args:
            query: Search query
            limit: Maximum number of results to return

        Returns:
            List of search results
        """
        # Generate embeddings for query
        e5_embedding = embedding_service.get_e5_embedding(query)
        sbert_embedding = embedding_service.get_sbert_embedding(query)

        # Search in both collections
        e5_results = qdrant_manager.search_e5(e5_embedding, limit=limit * 2)
        v2_results = qdrant_manager.search_v2(sbert_embedding, limit=limit * 2)

        # Merge results
        merged_results = self._merge_results(e5_results, v2_results, limit)

        return merged_results

    def _merge_results(
        self,
        e5_results: List[Dict[str, Any]],
        v2_results: List[Dict[str, Any]],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """
        Merge results from both collections

        Args:
            e5_results: Results from E5 collection
            v2_results: Results from V2 collection
            limit: Maximum number of results to return

        Returns:
            Merged results
        """
        # Create a dictionary to store the best score for each segment
        best_scores = {}

        # Process E5 results
        for result in e5_results:
            segment_id = result.id
            score = result.score
            payload = result.payload

            key = f"{payload['episode_id']}-{payload['seg_no']:04d}"

            if key not in best_scores or score > best_scores[key]["score"]:
                best_scores[key] = {"score": score, "payload": payload, "model": "e5"}

        # Process V2 results
        for result in v2_results:
            segment_id = result.id
            score = result.score
            payload = result.payload

            key = f"{payload['episode_id']}-{payload['seg_no']:04d}"

            if key not in best_scores or score > best_scores[key]["score"]:
                best_scores[key] = {"score": score, "payload": payload, "model": "v2"}

        # Convert to list and sort by score
        results_list = [
            {
                "id": key,
                "score": data["score"],
                "payload": data["payload"],
                "model": data["model"],
            }
            for key, data in best_scores.items()
        ]

        # Sort by score in descending order
        results_list.sort(key=lambda x: x["score"], reverse=True)

        # Limit results
        return results_list[:limit]


# Singleton instance
search_service = SearchService()
