"""User service - Business logic for user operations"""

import logging
from datetime import datetime, timezone
from typing import Any

from app.repositories.user import UserRepository

logger = logging.getLogger(__name__)


class UserService:
    """Service for user-related business logic"""

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def get_or_create_default_user(self) -> dict[str, Any]:
        """
        Get or create the default user
        
        Returns:
            User data
        """
        user = self.user_repo.find_by_email("default@default.com")

        if not user:
            # Create default user
            user_data = {
                "name": "default",
                "mail": "default@default.com",
                "activeSince": datetime.now(tz=timezone.utc),
                "projectList": [],
                "folderList": [],
                "assistantList": [],
                "contributionHistory": [],
                "recent": [],
                "message": [],
                "badge": "Iron",
                "rank": 100,
            }

            user_id = self.user_repo.create(user_data)
            user_data["_id"] = user_id
            logger.info("Created default user")
            return user_data

        return user

    def get_all_users(self) -> list[dict[str, Any]]:
        """Get all users"""
        return self.user_repo.find_many()

    def update_recent_files(
        self, user_id: str, folder_id: str, file_id: str, folder_name: str, file_name: str
    ) -> bool:
        """
        Update user's recent files list
        
        Args:
            user_id: User ID
            folder_id: Folder ID
            file_id: File ID
            folder_name: Folder name
            file_name: File name
            
        Returns:
            True if successful
        """
        user = self.user_repo.find_by_id(user_id)
        if not user:
            return False

        recent_files = user.get("recent", [])

        # Check if this file is already in recent
        existing = any(
            r.get("folder") == folder_id and r.get("file") == file_id for r in recent_files
        )

        if not existing:
            recent_files.append(
                {
                    "folder": folder_id,
                    "file": file_id,
                    "displayText": f"{folder_name} - {file_name}",
                }
            )
            # Keep only last 5
            recent_files = recent_files[-5:]
            self.user_repo.update_recent_files(user_id, recent_files)

        return True

    def share_folder_with_user(
        self, target_user_id: str, folder: dict, sender_name: str, message: str
    ) -> bool:
        """
        Share a folder with another user
        
        Args:
            target_user_id: ID of user to share with
            folder: Folder data
            sender_name: Name of user sharing
            message: Share message
            
        Returns:
            True if successful
        """
        user = self.user_repo.find_by_id(target_user_id)
        if not user:
            return False

        folder_id = str(folder["_id"])
        project_id = folder["project"]["id"]

        # Add folder if not already in user's list
        if folder_id not in user.get("folderList", []):
            self.user_repo.add_folder(target_user_id, folder_id)
            self.user_repo.add_message(
                target_user_id,
                {
                    "folder": folder_id,
                    "displayText": f'From {sender_name}: Folder {folder["name"]} is shared to you. {message}',
                },
            )

        # Add project if not already in user's list
        if project_id not in user.get("projectList", []):
            self.user_repo.add_project(target_user_id, project_id)

        logger.info(f"Shared folder {folder_id} with user {target_user_id}")
        return True

    def share_project_with_user(
        self, target_user_id: str, project: dict, sender_name: str, message: str
    ) -> bool:
        """
        Share a project with another user
        
        Args:
            target_user_id: ID of user to share with
            project: Project data
            sender_name: Name of user sharing
            message: Share message
            
        Returns:
            True if successful
        """
        user = self.user_repo.find_by_id(target_user_id)
        if not user:
            return False

        project_id = str(project["_id"])

        # Add project if not already in user's list
        if project_id not in user.get("projectList", []):
            self.user_repo.add_project(target_user_id, project_id)
            self.user_repo.add_message(
                target_user_id,
                {
                    "project": project_id,
                    "displayText": f'From {sender_name}: Project {project["projectName"]} is shared to you. {message}',
                },
            )

        logger.info(f"Shared project {project_id} with user {target_user_id}")
        return True

