"""Base repository with common CRUD operations"""

from typing import Any, Generic, TypeVar

from bson import ObjectId
from pymongo.database import Database

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """Base repository class with common database operations"""

    def __init__(self, db: Database, collection_name: str):
        """
        Initialize repository
        
        Args:
            db: Database instance
            collection_name: Name of the MongoDB collection
        """
        self.db = db
        self.collection = db[collection_name]
        self.collection_name = collection_name

    def find_by_id(self, id: str) -> dict[str, Any] | None:
        """
        Find document by ID
        
        Args:
            id: Document ID
            
        Returns:
            Document dict or None if not found
        """
        try:
            return self.collection.find_one({"_id": ObjectId(id)})
        except Exception:
            return None

    def find_one(self, filter: dict[str, Any]) -> dict[str, Any] | None:
        """
        Find one document matching filter
        
        Args:
            filter: MongoDB filter query
            
        Returns:
            Document dict or None if not found
        """
        return self.collection.find_one(filter)

    def find_many(
        self, filter: dict[str, Any] = {}, limit: int | None = None
    ) -> list[dict[str, Any]]:
        """
        Find multiple documents
        
        Args:
            filter: MongoDB filter query
            limit: Maximum number of documents to return
            
        Returns:
            List of document dicts
        """
        cursor = self.collection.find(filter)
        if limit:
            cursor = cursor.limit(limit)
        return list(cursor)

    def find_by_ids(self, ids: list[str]) -> list[dict[str, Any]]:
        """
        Find documents by list of IDs
        
        Args:
            ids: List of document IDs
            
        Returns:
            List of document dicts
        """
        try:
            object_ids = [ObjectId(id) for id in ids]
            return list(self.collection.find({"_id": {"$in": object_ids}}))
        except Exception:
            return []

    def create(self, data: dict[str, Any]) -> str:
        """
        Create a new document
        
        Args:
            data: Document data
            
        Returns:
            ID of created document
        """
        result = self.collection.insert_one(data)
        return str(result.inserted_id)

    def update_by_id(self, id: str, data: dict[str, Any]) -> bool:
        """
        Update document by ID
        
        Args:
            id: Document ID
            data: Update data
            
        Returns:
            True if document was modified, False otherwise
        """
        try:
            result = self.collection.update_one({"_id": ObjectId(id)}, {"$set": data})
            return result.modified_count > 0
        except Exception:
            return False

    def update_one(
        self, filter: dict[str, Any], update: dict[str, Any], array_filters: list | None = None
    ) -> bool:
        """
        Update one document matching filter
        
        Args:
            filter: MongoDB filter query
            update: Update operation
            array_filters: Array filters for nested updates
            
        Returns:
            True if document was modified, False otherwise
        """
        try:
            if array_filters:
                result = self.collection.update_one(filter, update, array_filters=array_filters)
            else:
                result = self.collection.update_one(filter, update)
            return result.modified_count > 0
        except Exception:
            return False

    def update_many(self, filter: dict[str, Any], update: dict[str, Any]) -> int:
        """
        Update multiple documents
        
        Args:
            filter: MongoDB filter query
            update: Update operation
            
        Returns:
            Number of documents modified
        """
        try:
            result = self.collection.update_many(filter, update)
            return result.modified_count
        except Exception:
            return 0

    def delete_by_id(self, id: str) -> bool:
        """
        Delete document by ID
        
        Args:
            id: Document ID
            
        Returns:
            True if document was deleted, False otherwise
        """
        try:
            result = self.collection.delete_one({"_id": ObjectId(id)})
            return result.deleted_count > 0
        except Exception:
            return False

    def delete_one(self, filter: dict[str, Any]) -> bool:
        """
        Delete one document matching filter
        
        Args:
            filter: MongoDB filter query
            
        Returns:
            True if document was deleted, False otherwise
        """
        try:
            result = self.collection.delete_one(filter)
            return result.deleted_count > 0
        except Exception:
            return False

    def delete_many(self, filter: dict[str, Any]) -> int:
        """
        Delete multiple documents
        
        Args:
            filter: MongoDB filter query
            
        Returns:
            Number of documents deleted
        """
        try:
            result = self.collection.delete_many(filter)
            return result.deleted_count
        except Exception:
            return 0

    def count(self, filter: dict[str, Any] = {}) -> int:
        """
        Count documents matching filter
        
        Args:
            filter: MongoDB filter query
            
        Returns:
            Number of matching documents
        """
        return self.collection.count_documents(filter)

