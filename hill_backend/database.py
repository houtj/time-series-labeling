"""
Database Connection
Simplified database module - only connection management
"""
import os
import pymongo
from bson.json_util import dumps
from bson.objectid import ObjectId

# Global database connection
_db = None
_data_folder_path = None


def init_database():
    """Initialize database connection and create indexes"""
    global _db, _data_folder_path
    
    MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://root:example@localhost:27017/")
    client = pymongo.MongoClient(MONGODB_URL)
    _db = client['hill_ts']
    _data_folder_path = os.getenv("DATA_FOLDER_PATH", './data_folder')
    
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
    global _data_folder_path
    if _data_folder_path is None:
        init_database()
    return _data_folder_path
