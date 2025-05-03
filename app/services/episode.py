from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.models import Episode, EpisodeSegment


class EpisodeService:
    """
    Service for retrieving and managing episode data
    """

    def get_episodes_list(
        self, page: int, per_page: int, db: Session
    ) -> Dict[str, Any]:
        """
        Get paginated list of episodes with their first segments

        Args:
            page: Page number (1-based)
            per_page: Number of episodes per page
            db: Database session

        Returns:
            Dictionary with episodes data and pagination info
        """
        # Calculate offset
        offset = (page - 1) * per_page

        # Query episodes with pagination
        episodes = (
            db.query(Episode)
            .order_by(Episode.created_at.desc())
            .offset(offset)
            .limit(per_page)
            .all()
        )

        # Get total count for pagination
        total_count = db.query(Episode).count()

        # Convert episodes to dict and get first segments
        episodes_data = []
        for episode in episodes:
            # Get basic episode data
            episode_data: Dict[str, Any] = {
                "id": episode.id,
                "name": episode.name,
                "media_type": episode.media_type,
                "ext": episode.ext or "mp3",  # Default to mp3 if ext is None
                "bytes": episode.bytes,
                "length": episode.length / 1000 if episode.length is not None else 0,
                "created_at": episode.created_at,
            }

            # Get first 3 segments
            segments = (
                db.query(EpisodeSegment)
                .filter(EpisodeSegment.episode_id == episode.id)
                .order_by(EpisodeSegment.seg_no)
                .limit(3)
                .all()
            )

            # Add segments to episode data
            episode_data["preview_segments"] = [
                {
                    "seg_no": segment.seg_no,
                    "text": segment.text,
                }
                for segment in segments
            ]

            episodes_data.append(episode_data)

        # Prepare pagination data
        total_pages = (total_count + per_page - 1) // per_page

        return {
            "episodes": episodes_data,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total_count": total_count,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
            },
        }

    def get_episode_by_hash(self, file_hash: str, db: Session) -> Optional[str]:
        """
        Get episode ID by file hash

        Args:
            file_hash: SHA256 hash of the file
            db: Database session

        Returns:
            Episode ID or None if not found
        """
        # Query episode by hash
        episode = db.query(Episode).filter(Episode.hash == file_hash).first()

        if not episode:
            return None

        return str(episode.id)

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
            "ext": episode.ext or "mp3",  # Default to mp3 if ext is None
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

    def delete_episode(self, episode_id: str, db: Session) -> bool:
        """
        Delete episode and all related data

        Args:
            episode_id: Episode ID
            db: Database session

        Returns:
            True if episode was deleted, False otherwise
        """
        # Query episode
        episode = db.query(Episode).filter(Episode.id == episode_id).first()

        if not episode:
            return False

        # Delete segments
        db.query(EpisodeSegment).filter(
            EpisodeSegment.episode_id == episode_id
        ).delete()

        # Delete episode
        db.delete(episode)
        db.commit()

        return True


# Singleton instance
episode_service = EpisodeService()
