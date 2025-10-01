"""Conversation repository for database operations"""

from pymongo.database import Database

from app.repositories.base import BaseRepository


class ConversationRepository(BaseRepository):
    """Repository for conversation-related database operations"""

    def __init__(self, db: Database):
        super().__init__(db, "conversations")

    def find_by_file_id(self, file_id: str) -> dict | None:
        """Find conversation by file ID"""
        return self.find_one({"fileId": file_id})

    def create_for_file(self, file_id: str) -> str:
        """Create a new conversation for a file"""
        return self.create({"fileId": file_id, "history": []})

    def update_history(self, file_id: str, history: list[dict]) -> bool:
        """Update conversation history"""
        return self.update_one({"fileId": file_id}, {"$set": {"history": history}})

    def clear_history(self, file_id: str) -> bool:
        """Clear conversation history"""
        return self.update_one({"fileId": file_id}, {"$set": {"history": []}})

