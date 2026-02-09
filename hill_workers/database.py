"""
Database Connection Management
Handles MongoDB connection and provides database access
"""
import pymongo

from config import settings

# Global database connection
_db = None


def init_database():
    """Initialize database connection"""
    global _db
    client = pymongo.MongoClient(settings.MONGODB_URL)
    _db = client[settings.DATABASE_NAME]
    return _db


def get_db():
    """Get database instance"""
    global _db
    if _db is None:
        init_database()
    return _db


def get_data_folder_path():
    """Get data folder path"""
    return str(settings.DATA_FOLDER_PATH)

