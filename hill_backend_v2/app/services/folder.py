"""Folder service - Business logic for folder operations"""

import logging
import shutil
from pathlib import Path
from typing import Any

from app.core.config import get_settings
from app.core.exceptions import NotFoundException
from app.repositories.folder import FolderRepository
from app.repositories.label import LabelRepository
from app.repositories.file import FileRepository
from app.repositories.user import UserRepository

logger = logging.getLogger(__name__)
settings = get_settings()


class FolderService:
    """Service for folder-related business logic"""

    def __init__(
        self,
        folder_repo: FolderRepository,
        user_repo: UserRepository,
        file_repo: FileRepository,
        label_repo: LabelRepository,
    ):
        self.folder_repo = folder_repo
        self.user_repo = user_repo
        self.file_repo = file_repo
        self.label_repo = label_repo
        self.data_folder = Path(settings.data_folder_path)

    def create_folder(
        self, folder_name: str, project: dict, template: dict, user_id: str
    ) -> dict[str, Any]:
        """
        Create a new folder
        
        Args:
            folder_name: Name of the folder
            project: Project reference {id, name}
            template: Template reference {id, name}
            user_id: ID of the user creating the folder
            
        Returns:
            Created folder data
            
        Raises:
            NotFoundException: If user not found
        """
        # Verify user exists
        user = self.user_repo.find_by_id(user_id)
        if not user:
            raise NotFoundException("User", user_id)

        # Create folder
        new_folder = {
            "name": folder_name,
            "project": {"id": project["id"], "name": project["name"]},
            "template": {"id": template["id"], "name": template["name"]},
            "fileList": [],
            "nbLabeledFiles": 0,
            "nbTotalFiles": 0,
        }

        folder_id = self.folder_repo.create(new_folder)

        # Add folder to user's list
        self.user_repo.add_folder(user_id, folder_id)

        logger.info(f"Created folder {folder_id} for user {user_id}")
        return {"success": True, "folder_id": folder_id}

    def get_folders(self, folder_ids: list[str]) -> list[dict[str, Any]]:
        """Get multiple folders by IDs"""
        return self.folder_repo.find_by_ids(folder_ids)

    def get_folder(self, folder_id: str) -> dict[str, Any]:
        """
        Get folder by ID
        
        Args:
            folder_id: Folder ID
            
        Returns:
            Folder data
            
        Raises:
            NotFoundException: If folder not found
        """
        folder = self.folder_repo.find_by_id(folder_id)
        if not folder:
            raise NotFoundException("Folder", folder_id)
        return folder

    def delete_folder(self, folder_id: str) -> bool:
        """
        Delete a folder and all its files
        
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

        # Get labels to delete
        files = self.file_repo.find_by_folder(file_ids)
        label_ids = [file["label"] for file in files if "label" in file]

        # Delete labels
        if label_ids:
            self.label_repo.delete_many({"_id": {"$in": label_ids}})

        # Delete files
        if file_ids:
            self.file_repo.delete_many({"_id": {"$in": file_ids}})

        # Remove folder from all users
        self.user_repo.remove_folder(folder_id)

        # Delete folder
        self.folder_repo.delete_by_id(folder_id)

        # Delete folder from disk
        folder_path = self.data_folder / folder_id
        if folder_path.exists():
            shutil.rmtree(folder_path, ignore_errors=True)

        logger.info(f"Deleted folder {folder_id}")
        return True

