"""File service - Business logic for file operations"""

import json
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import aiofiles
import pandas as pd
from fastapi import UploadFile

from app.core.config import get_settings
from app.core.exceptions import NotFoundException, ValidationException
from app.repositories.file import FileRepository
from app.repositories.folder import FolderRepository
from app.repositories.label import LabelRepository

logger = logging.getLogger(__name__)
settings = get_settings()


class FileService:
    """Service for file-related business logic"""

    def __init__(
        self, file_repo: FileRepository, label_repo: LabelRepository, folder_repo: FolderRepository
    ):
        self.file_repo = file_repo
        self.label_repo = label_repo
        self.folder_repo = folder_repo
        self.data_folder = Path(settings.data_folder_path)

    async def upload_files(
        self, folder_id: str, files: list[UploadFile], user_name: str
    ) -> dict[str, Any]:
        """
        Upload multiple files to a folder
        
        Args:
            folder_id: Folder ID
            files: List of uploaded files
            user_name: Name of the user uploading
            
        Returns:
            Upload result information
            
        Raises:
            NotFoundException: If folder not found
        """
        folder = self.folder_repo.find_by_id(folder_id)
        if not folder:
            raise NotFoundException("Folder", folder_id)

        uploaded_count = 0

        for file in files:
            # Create label
            label_data = {"events": [], "guidelines": []}
            label_id = self.label_repo.create(label_data)

            # Create file metadata
            file_data = {
                "name": file.filename,
                "parsing": "uploading",
                "nbEvent": "unlabeled",
                "description": "",
                "rawPath": "",
                "jsonPath": "",
                "lastModifier": user_name,
                "lastUpdate": datetime.now(tz=timezone.utc),
                "label": label_id,
            }

            file_id = self.file_repo.create(file_data)

            # Save file to disk
            file_path = self.data_folder / folder_id / file_id
            file_path.mkdir(parents=True, exist_ok=True)

            full_file_path = file_path / file.filename
            async with aiofiles.open(full_file_path, "wb") as f:
                content = await file.read()
                await f.write(content)

            # Update file with paths
            raw_path = f"{folder_id}/{file_id}/{file.filename}"
            self.file_repo.update_by_id(file_id, {"rawPath": raw_path, "parsing": "parsing start"})

            # Add file to folder
            self.folder_repo.add_file(folder_id, file_id)

            uploaded_count += 1
            logger.info(f"Uploaded file {file_id} to folder {folder_id}")

        return {"success": True, "uploaded": uploaded_count}

    def get_file(self, file_id: str) -> dict[str, Any]:
        """
        Get file metadata and data
        
        Args:
            file_id: File ID
            
        Returns:
            File information and data
            
        Raises:
            NotFoundException: If file not found
        """
        file = self.file_repo.find_by_id(file_id)
        if not file:
            raise NotFoundException("File", file_id)

        # Read JSON data if available
        data = None
        if file.get("jsonPath"):
            json_path = self.data_folder / file["jsonPath"]
            try:
                with open(json_path, "r") as f:
                    data = json.load(f)
            except Exception as e:
                logger.warning(f"Could not read JSON for file {file_id}: {e}")

        return {"fileInfo": file, "data": data}

    def get_files(self, file_ids: list[str]) -> list[dict[str, Any]]:
        """Get multiple files by IDs"""
        return self.file_repo.find_by_ids(file_ids)

    def delete_file(self, file_id: str) -> bool:
        """
        Delete a file and its associated data
        
        Args:
            file_id: File ID
            
        Returns:
            True if successful
            
        Raises:
            NotFoundException: If file not found
        """
        file = self.file_repo.find_by_id(file_id)
        if not file:
            raise NotFoundException("File", file_id)

        # Delete label
        if file.get("label"):
            self.label_repo.delete_by_id(file["label"])

        # Find and update folder
        folder = self.folder_repo.find_by_file_id(file_id)
        if folder:
            was_labeled = file.get("nbEvent") != "unlabeled"
            self.folder_repo.remove_file(str(folder["_id"]), file_id, was_labeled)

        # Delete file from database
        self.file_repo.delete_by_id(file_id)

        # Delete files from disk
        if folder:
            folder_id = str(folder["_id"])
            file_folder_path = self.data_folder / folder_id / file_id
            if file_folder_path.exists():
                shutil.rmtree(file_folder_path, ignore_errors=True)

        logger.info(f"Deleted file {file_id}")
        return True

    def update_description(self, file_id: str, description: str) -> bool:
        """
        Update file description
        
        Args:
            file_id: File ID
            description: New description
            
        Returns:
            True if successful
            
        Raises:
            NotFoundException: If file not found
        """
        file = self.file_repo.find_by_id(file_id)
        if not file:
            raise NotFoundException("File", file_id)

        self.file_repo.update_by_id(file_id, {"description": description})
        logger.info(f"Updated description for file {file_id}")
        return True

    def reparse_files(self, folder_id: str) -> bool:
        """
        Mark all files in a folder for reparsing
        
        Args:
            folder_id: Folder ID
            
        Returns:
            True if successful
            
        Raises:
            NotFoundException: If folder not found
        """
        folder = self.folder_repo.find_by_id(folder_id)
        if not folder:
            raise NotFoundException("Folder", folder_id)

        file_ids = folder.get("fileList", [])
        count = self.file_repo.update_many(
            {"_id": {"$in": [self.file_repo.collection.database.client.address for id in file_ids]}},
            {"$set": {"parsing": "parsing start"}},
        )

        logger.info(f"Marked {count} files for reparsing in folder {folder_id}")
        return True

    def get_files_data(self, folder_id: str) -> list[dict[str, Any]]:
        """
        Get all file data for a folder
        
        Args:
            folder_id: Folder ID
            
        Returns:
            List of file data
            
        Raises:
            NotFoundException: If folder not found
        """
        folder = self.folder_repo.find_by_id(folder_id)
        if not folder:
            raise NotFoundException("Folder", folder_id)

        files = self.file_repo.find_by_folder(folder.get("fileList", []))
        response = []

        for file in files:
            if file.get("parsing") == "parsed" and file.get("jsonPath"):
                json_path = self.data_folder / file["jsonPath"]
                try:
                    with open(json_path, "r") as f:
                        data = json.load(f)
                    response.append({"file_name": file["name"], "data": data})
                except Exception as e:
                    logger.warning(f"Could not read file {file['_id']}: {e}")

        return response

    def get_files_events(self, folder_id: str) -> list[dict[str, Any]]:
        """
        Get all events for files in a folder
        
        Args:
            folder_id: Folder ID
            
        Returns:
            List of file events
            
        Raises:
            NotFoundException: If folder not found
        """
        folder = self.folder_repo.find_by_id(folder_id)
        if not folder:
            raise NotFoundException("Folder", folder_id)

        files = self.file_repo.find_by_folder(folder.get("fileList", []))
        response = []

        for file in files:
            if file.get("parsing") == "parsed" and file.get("label"):
                label = self.label_repo.find_by_id(file["label"])
                if label:
                    response.append({"file_name": file["name"], "events": label.get("events", [])})

        return response

