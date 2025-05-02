import mimetypes
import uuid
from typing import Any, BinaryIO, Dict

from sqlalchemy.orm import Session

from app.models.models import Episode, EpisodeSegment
from app.services.embedding import embedding_service
from app.services.storage import storage_service
from app.transcriber.transcriber import transcriber_service
from app.vectorstore.qdrant import qdrant_manager


class UploadService:
    """
    Service for handling file uploads, transcription, and vectorization
    """

    def __init__(self):
        # Supported media types
        self.supported_media_types = [
            "audio/mpeg",  # mp3
            "audio/wav",  # wav
            "audio/x-m4a",  # m4a
            "audio/mp4",  # m4a alternative
        ]

    def process_upload(self, file: BinaryIO, filename: str, db: Session) -> str:
        """
        Process uploaded file

        Args:
            file: File-like object
            filename: Original filename
            db: Database session

        Returns:
            Episode ID
        """
        # Generate UUID for the episode
        episode_id = str(uuid.uuid4())

        # Get media type and extension
        media_type = self._get_media_type(filename)
        extension = self._get_extension(media_type)

        # Check if media type is supported
        if media_type not in self.supported_media_types:
            raise ValueError(f"Unsupported media type: {media_type}")

        # Save file to storage
        file_path, file_size = storage_service.save_file(file, episode_id, extension)

        # Create episode record
        episode = Episode(
            id=episode_id,
            media_type=media_type,
            name=filename,
            bytes=file_size,
            length=None,  # Will be updated after transcription
        )
        db.add(episode)
        db.commit()

        # Transcribe audio
        transcription = transcriber_service.transcribe(file_path)

        # Process transcription chunks
        self._process_transcription(transcription, episode_id, db)

        # Update episode length if available
        if "duration" in transcription:
            # save as ms
            episode.length = int(float(transcription["duration"]) * 1000)  # type: ignore
            db.commit()

        return episode_id

    def _get_media_type(self, filename: str) -> str | None:
        """
        Get media type from filename
        """
        media_type, _ = mimetypes.guess_type(filename)
        return media_type

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

    def _process_transcription(
        self, transcription: Dict[str, Any], episode_id: str, db: Session
    ):
        """
        Process transcription chunks
        """
        # Get chunks from transcription
        chunks = transcription.get("chunks", [])

        # Process each chunk
        for seg_no, chunk in enumerate(chunks):
            # Extract text and timestamps
            text = chunk.get("text", "")
            timestamps = chunk.get("timestamp", [0, 0])
            # ms
            start_time = timestamps[0] if timestamps[0] is not None else 0
            end_time = timestamps[1] if timestamps[1] is not None else 0
            start_time = int(float(start_time) * 1000)
            end_time = int(float(end_time) * 1000)

            # Create segment record
            segment = EpisodeSegment(
                episode_id=episode_id,
                seg_no=seg_no,
                start=start_time,
                end=end_time,
                text=text,
            )
            db.add(segment)

            # Generate embeddings
            e5_embedding = embedding_service.get_e5_embedding(text)
            sbert_embedding = embedding_service.get_sbert_embedding(text)

            # Create payload for vector stores
            payload = {
                "start": start_time,
                "end": end_time,
                "text": text,
                "episode_id": episode_id,
                "seg_no": seg_no,
                "segment_id": f"{episode_id}-{seg_no:04d}",
            }

            # Add to vector stores

            qdrant_manager.add_segment_e5(e5_embedding, payload)
            qdrant_manager.add_segment_v2(sbert_embedding, payload)

        # Commit all segments
        db.commit()


# Singleton instance
upload_service = UploadService()
