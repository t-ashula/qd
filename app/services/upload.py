import hashlib
import mimetypes
import uuid
from typing import Any, BinaryIO, Dict, Optional, Tuple

import magic
from sqlalchemy.orm import Session

from app.models.models import Episode, EpisodeSegment, TranscribeHistory
from app.services.embedding import embedding_service
from app.services.episode import episode_service
from app.services.storage import storage_service
from app.transcriber.transcriber import DEFAULT_MODEL, transcriber_service
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

    def cleanup_resources(self, episode_id: str, extension: str, db: Session):
        """
        Clean up resources when upload fails

        This method deletes:
        - Episode record from database
        - TranscribeHistory records from database
        - EpisodeSegment records from database
        - Points from Qdrant collections
        - Uploaded file from storage

        Args:
            episode_id: Episode ID to clean up
            extension: File extension for the uploaded file
            db: Database session
        """
        try:
            # Delete points from Qdrant collections
            try:
                qdrant_manager.delete_points_by_episode_id(episode_id)
            except Exception as e:
                # Log error but continue cleanup
                print(f"Error deleting Qdrant points: {str(e)}")

            # Delete uploaded file
            try:
                storage_service.delete_file(episode_id, extension)
            except Exception as e:
                # Log error but continue cleanup
                print(f"Error deleting file: {str(e)}")

            # Delete database records
            try:
                # Delete segments first to avoid foreign key constraint errors
                db.query(EpisodeSegment).filter(
                    EpisodeSegment.episode_id == episode_id
                ).delete()

                # Delete transcribe histories
                db.query(TranscribeHistory).filter(
                    TranscribeHistory.episode_id == episode_id
                ).delete()

                # Delete episode
                db.query(Episode).filter(Episode.id == episode_id).delete()

                # Commit changes
                db.commit()
            except Exception as e:
                # Log error but continue cleanup
                print(f"Error deleting database records: {str(e)}")
                # Rollback in case of error
                db.rollback()

        except Exception as e:
            # Log any unexpected errors during cleanup
            print(f"Unexpected error during cleanup: {str(e)}")

    def process_upload(
        self,
        file: BinaryIO,
        filename: str,
        db: Session,
        model_name: str = DEFAULT_MODEL,
    ) -> str:
        """
        Process uploaded file

        Args:
            file: File-like object
            filename: Original filename
            db: Database session
            model_name: Name of the transcription model to use

        Returns:
            Episode ID
        """
        episode_id = None
        extension = None

        try:
            # Get media type and extension
            media_type, extension = self._detect_media_type_and_extension(
                file, filename
            )

            # Check if media type is supported
            if media_type not in self.supported_media_types:
                raise ValueError(f"Unsupported media type: {media_type}")

            # Calculate file hash and check if already exists
            file_hash, file_content = self._calculate_file_hash(file)
            existing_episode_id = episode_service.get_episode_by_hash(file_hash, db)

            if existing_episode_id:
                # File already exists, return existing episode ID
                return existing_episode_id

            # Generate UUID for the new episode
            episode_id = str(uuid.uuid4())

            # Save file to storage
            file_path, file_size = storage_service.save_file_from_bytes(
                file_content, episode_id, extension
            )

            # Create episode record
            episode = Episode(
                id=episode_id,
                media_type=media_type,
                name=filename,
                bytes=file_size,
                hash=file_hash,
                ext=extension,
                length=None,  # Will be updated after transcription
            )
            db.add(episode)
            db.commit()

            # Transcribe audio with specified model
            transcription = transcriber_service.transcribe(file_path, model_name)

            # Create transcribe history record
            transcribe_history = TranscribeHistory(
                episode_id=episode_id,
                model_name=model_name,
            )
            db.add(transcribe_history)
            db.flush()  # Get ID without committing

            # Process transcription chunks
            self._process_transcription(
                transcription, episode_id, int(transcribe_history.id), db
            )

            # Update episode length if available
            if "duration" in transcription:
                # save as ms
                episode.length = int(float(transcription["duration"]) * 1000)  # type: ignore
                db.commit()

            return episode_id

        except Exception as e:
            # If an error occurs after resources have been created, clean them up
            if episode_id and extension:
                # Rollback any uncommitted database changes
                db.rollback()

                # Clean up resources
                self.cleanup_resources(episode_id, extension, db)

            # Re-raise the exception
            raise

    def _calculate_file_hash(self, file: BinaryIO) -> Tuple[str, bytes]:
        """
        Calculate SHA256 hash of file

        Args:
            file: File-like object

        Returns:
            Tuple of (hash_string, file_content)
        """
        # Read the entire file content
        file_content = file.read()

        # Calculate SHA256 hash
        sha256_hash = hashlib.sha256(file_content).hexdigest()

        # Reset file pointer to beginning
        file.seek(0)

        return sha256_hash, file_content

    def _detect_media_type_and_extension(
        self, file: BinaryIO, filename: str
    ) -> Tuple[str, str]:
        """
        Detect media type and extension using multiple methods:
        1. python-magic (libmagic)
        2. Filename extension (mimetypes)
        3. Default to audio/mpeg and mp3 if unknown

        Args:
            file: File-like object
            filename: Original filename

        Returns:
            Tuple of (media_type, extension)
        """
        # Method 1: Try to detect using python-magic
        try:
            # Save current position
            current_position = file.tell()

            # Read a sample of the file for magic detection
            sample = file.read(2048)

            # Reset to original position
            file.seek(current_position)

            # Detect mime type using magic
            mime_type = magic.from_buffer(sample, mime=True)

            if mime_type in self.supported_media_types:
                # Get extension from detected mime type
                if mime_type == "audio/mpeg":
                    return mime_type, "mp3"
                elif mime_type == "audio/wav":
                    return mime_type, "wav"
                elif mime_type in ["audio/x-m4a", "audio/mp4"]:
                    return mime_type, "m4a"
        except Exception:
            # If magic detection fails, continue to next method
            pass

        # Method 2: Try to detect from filename
        media_type, _ = mimetypes.guess_type(filename)
        if media_type is not None and media_type in self.supported_media_types:
            # Get extension from filename
            ext = filename.split(".")[-1].lower() if "." in filename else ""
            if ext in ["mp3", "wav", "m4a"]:
                return media_type, ext

        # Method 3: Default to audio/mpeg and mp3
        return "audio/mpeg", "mp3"

    def _process_transcription(
        self,
        transcription: Dict[str, Any],
        episode_id: str,
        transcribe_history_id: int,
        db: Session,
    ):
        """
        Process transcription chunks

        Args:
            transcription: Transcription result
            episode_id: Episode ID
            transcribe_history_id: Transcribe history ID
            db: Database session
        """
        # Get chunks from transcription
        chunks = transcription.get("chunks", [])
        model_name = transcription.get("model_name", DEFAULT_MODEL)

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
                transcribe_history_id=transcribe_history_id,
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
                "transcribe_history_id": transcribe_history_id,
                "model_name": model_name,
            }

            # Add to vector stores
            qdrant_manager.add_segment_e5(e5_embedding, payload)
            qdrant_manager.add_segment_v2(sbert_embedding, payload)

        # Commit all segments
        db.commit()


# Singleton instance
upload_service = UploadService()
