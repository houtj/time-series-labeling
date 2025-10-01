"""Folder repository for database operations"""

from bson import ObjectId
from pymongo.database import Database

from app.repositories.base import BaseRepository


class FolderRepository(BaseRepository):
    """Repository for folder-related database operations"""

    def __init__(self, db: Database):
        super().__init__(db, "folders")

    def add_file(self, folder_id: str, file_id: str) -> bool:
        """Add a file to a folder"""
        return self.update_one(
            {"_id": ObjectId(folder_id)},
            {"$push": {"fileList": file_id}, "$inc": {"nbTotalFiles": 1}},
        )

    def remove_file(self, folder_id: str, file_id: str, was_labeled: bool) -> bool:
        """Remove a file from a folder"""
        update = {"$pull": {"fileList": file_id}, "$inc": {"nbTotalFiles": -1}}
        if was_labeled:
            update["$inc"]["nbLabeledFiles"] = -1
        return self.update_one({"_id": ObjectId(folder_id)}, update)

    def increment_labeled_files(self, folder_id: str) -> bool:
        """Increment the labeled files counter"""
        return self.update_one({"_id": ObjectId(folder_id)}, {"$inc": {"nbLabeledFiles": 1}})

    def find_by_file_id(self, file_id: str) -> dict | None:
        """Find folder containing a specific file"""
        return self.find_one({"fileList": file_id})

