import os
import shutil
from pathlib import Path
from typing import BinaryIO, Tuple, Union

# Media storage directory
MEDIA_DIR = os.getenv("MEDIA_DIR", "media")


class StorageService:
    """
    Service for file storage operations
    """

    def __init__(self):
        # Create media directory if it doesn't exist
        os.makedirs(MEDIA_DIR, exist_ok=True)

    def save_file(
        self, file: BinaryIO, file_id: str, extension: str
    ) -> Tuple[str, int]:
        """
        Save file to storage

        Args:
            file: File-like object
            file_id: Unique file ID
            extension: File extension

        Returns:
            Tuple of file path and file size
        """
        # Create file path
        file_path = os.path.join(MEDIA_DIR, f"{file_id}.{extension}")

        # Save file
        with open(file_path, "wb") as f:
            # Read file in chunks to avoid memory issues
            shutil.copyfileobj(file, f)

        # Get file size
        file_size = os.path.getsize(file_path)

        return file_path, file_size

    def save_file_from_bytes(
        self, file_content: bytes, file_id: str, extension: str
    ) -> Tuple[str, int]:
        """
        Save file content to storage

        Args:
            file_content: File content as bytes
            file_id: Unique file ID
            extension: File extension

        Returns:
            Tuple of file path and file size
        """
        # Create file path
        file_path = os.path.join(MEDIA_DIR, f"{file_id}.{extension}")

        # Save file
        with open(file_path, "wb") as f:
            f.write(file_content)

        # Get file size
        file_size = os.path.getsize(file_path)

        return file_path, file_size

    def get_file_path(self, file_id: str, extension: str) -> str:
        """
        Get file path

        Args:
            file_id: Unique file ID
            extension: File extension

        Returns:
            File path
        """
        return os.path.join(MEDIA_DIR, f"{file_id}.{extension}")

    def file_exists(self, file_id: str, extension: str) -> bool:
        """
        Check if file exists

        Args:
            file_id: Unique file ID
            extension: File extension

        Returns:
            True if file exists, False otherwise
        """
        file_path = self.get_file_path(file_id, extension)
        return os.path.exists(file_path)

    def delete_file(self, file_id: str, extension: str) -> bool:
        """
        Delete file

        Args:
            file_id: Unique file ID
            extension: File extension

        Returns:
            True if file was deleted, False otherwise
        """
        file_path = self.get_file_path(file_id, extension)
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False


# Singleton instance
storage_service = StorageService()
