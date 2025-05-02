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
        episode_length = episode.length / 1000 if episode.length is not None else 0
        episode_data = {
            "id": episode.id,
            "media_type": episode.media_type,
            "ext": self._get_extension(episode.media_type),  # type: ignore
            "name": episode.name,
            "bytes": episode.bytes,
            "length": episode_length,
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
                "start": segment.start / 1000 if segment.start is not None else 0,
                "end": segment.end / 1000 if segment.end is not None else 0,
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

    # TODO: unify UploadService, or save extension as column
    def _get_extension(self, media_type: str | None) -> str:
        """
        Get file extension from media type
        """
        if media_type == "audio/mpeg":
            return "mp3"
        elif media_type == "audio/wav":
            return "wav"
        elif media_type in ["audio/x-m4a", "audio/mp4"]:
            return "m4a"
        else:
            # Default extension
            return "mp3"


# Singleton instance
episode_service = EpisodeService()
