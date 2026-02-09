"""
Database Connection
Simplified database module - only connection management
"""
import pymongo
from bson.json_util import dumps
from bson.objectid import ObjectId

from config import settings

# Global database connection
_db = None


def init_database():
    """Initialize database connection and create indexes"""
    global _db

    client = pymongo.MongoClient(settings.MONGODB_URL)
    _db = client[settings.DATABASE_NAME]

    # Create indexes for conversations
    _db['chat_conversations'].create_index('fileId', unique=True)
    _db['auto_detection_conversations'].create_index('fileId', unique=True)

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
