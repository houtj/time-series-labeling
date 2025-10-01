"""File repository for database operations"""

from bson import ObjectId
from pymongo.database import Database

from app.repositories.base import BaseRepository


class FileRepository(BaseRepository):
    """Repository for file-related database operations"""

    def __init__(self, db: Database):
        super().__init__(db, "files")

    def find_by_label_id(self, label_id: str) -> dict | None:
        """Find file by label ID"""
        return self.find_one({"label": label_id})

    def find_by_folder(self, file_ids: list[str]) -> list[dict]:
        """Find all files in a folder"""
        return self.find_by_ids(file_ids)

    def update_parsing_status(self, file_id: str, status: str) -> bool:
        """Update file parsing status"""
        return self.update_by_id(file_id, {"parsing": status})

