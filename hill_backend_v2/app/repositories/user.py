"""User repository for database operations"""

from bson import ObjectId
from pymongo.database import Database

from app.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    """Repository for user-related database operations"""

    def __init__(self, db: Database):
        super().__init__(db, "users")

    def find_by_email(self, email: str) -> dict | None:
        """Find user by email"""
        return self.find_one({"mail": email})

    def add_project(self, user_id: str, project_id: str) -> bool:
        """Add a project to user's project list"""
        return self.update_one({"_id": ObjectId(user_id)}, {"$push": {"projectList": project_id}})

    def add_folder(self, user_id: str, folder_id: str) -> bool:
        """Add a folder to user's folder list"""
        return self.update_one({"_id": ObjectId(user_id)}, {"$push": {"folderList": folder_id}})

    def add_message(self, user_id: str, message: dict) -> bool:
        """Add a message to user's message list"""
        return self.update_one({"_id": ObjectId(user_id)}, {"$push": {"message": message}})

    def update_recent_files(self, user_id: str, recent_files: list[dict]) -> bool:
        """Update user's recent files list"""
        return self.update_by_id(user_id, {"recent": recent_files})

    def remove_folder(self, folder_id: str) -> int:
        """Remove folder from all users"""
        return self.update_many(
            {"folderList": folder_id}, {"$pull": {"folderList": folder_id}}
        )

