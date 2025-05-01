from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.models import Episode, EpisodeSegment


class EpisodeService:
    """
    Service for retrieving episode data
    """

    def get_episode(self, episode_id: str, db: Session) -> Optional[Dict[str, Any]]:
        """
        Get episode data

        Args:
            episode_id: Episode ID
            db: Database session

        Returns:
            Episode data or None if not found
        """
        # Query episode
        episode = db.query(Episode).filter(Episode.id == episode_id).first()

        if not episode:
            return None

        # Convert to dict
        episode_data = {
            "id": episode.id,
            "media_type": episode.media_type,
            "name": episode.name,
            "bytes": episode.bytes,
            "length": episode.length,
            "created_at": episode.created_at,
        }

        return episode_data

    def get_episode_segments(
        self, episode_id: str, db: Session
    ) -> List[Dict[str, Any]]:
        """
        Get episode segments

        Args:
            episode_id: Episode ID
            db: Database session

        Returns:
            List of episode segments
        """
        # Query segments
        segments = (
            db.query(EpisodeSegment)
            .filter(EpisodeSegment.episode_id == episode_id)
            .order_by(EpisodeSegment.seg_no)
            .all()
        )

        # Convert to list of dicts
        segments_data = [
            {
                "id": segment.id,
                "episode_id": segment.episode_id,
                "seg_no": segment.seg_no,
                "start": segment.start,
                "end": segment.end,
                "text": segment.text,
                "created_at": segment.created_at,
            }
            for segment in segments
        ]

        return segments_data

    def get_episode_with_segments(
        self, episode_id: str, db: Session
    ) -> Optional[Dict[str, Any]]:
        """
        Get episode data with segments

        Args:
            episode_id: Episode ID
            db: Database session

        Returns:
            Episode data with segments or None if not found
        """
        # Get episode data
        episode_data = self.get_episode(episode_id, db)

        if not episode_data:
            return None

        # Get segments
        segments_data = self.get_episode_segments(episode_id, db)

        # Add segments to episode data
        episode_data["segments"] = segments_data

        return episode_data


# Singleton instance
episode_service = EpisodeService()
