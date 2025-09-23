import os
import pymongo
from bson.json_util import dumps
from bson.objectid import ObjectId

# Global database connection
_db = None
_data_folder_path = None

def init_database():
    """Initialize database connection"""
    global _db, _data_folder_path
    CHANGE_STREAM_DB = os.getenv("MONGODB_URL", "mongodb://root:example@localhost:27017/")
    client = pymongo.MongoClient(CHANGE_STREAM_DB)
    _db = client['hill_ts']
    _data_folder_path = os.getenv("DATA_FOLDER_PATH", './data_folder')
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

# Conversation database operations
def get_conversation(file_id: str):
    """Get conversation history for a file"""
    db = get_db()
    conversation = db['conversations'].find_one({'fileId': file_id})
    if conversation:
        return dumps(conversation)
    else:
        # Create new conversation if none exists
        new_conversation = {
            'fileId': file_id,
            'history': []
        }
        result = db['conversations'].insert_one(new_conversation)
        new_conversation['_id'] = result.inserted_id
        return dumps(new_conversation)

def clear_conversation(file_id: str):
    """Clear conversation history for a file"""
    db = get_db()
    result = db['conversations'].update_one(
        {'fileId': file_id}, 
        {'$set': {'history': []}}
    )
    return 'done'

def update_conversation_history(file_id: str, history: list):
    """Update conversation history in database"""
    db = get_db()
    result = db['conversations'].update_one(
        {'fileId': file_id},
        {'$set': {'history': history}}
    )
    return result
