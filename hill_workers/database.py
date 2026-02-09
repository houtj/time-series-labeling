"""
Database Connection Management
Handles MongoDB connection and provides database access
"""
import os
import pymongo
from dotenv import load_dotenv

load_dotenv()

# Global database connection
_db = None
_data_folder_path = None

def init_database():
    """Initialize database connection"""
    global _db, _data_folder_path
    MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://root:example@localhost:27017/")
    client = pymongo.MongoClient(MONGODB_URL)
    _db = client['hill_ts']
    _data_folder_path = os.getenv("DATA_FOLDER_PATH", '/home/thou2/projects/hill-app/app_data')
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

