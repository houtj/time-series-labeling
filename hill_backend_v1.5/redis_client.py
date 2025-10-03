"""
Redis Client for Task Queue Management
Backend uses this to add tasks to the queue
"""
import redis
import logging
from typing import Optional, Dict
from config import settings

logger = logging.getLogger(__name__)


class RedisQueueClient:
    """Redis Streams client for adding tasks to queue"""
    
    # Queue names
    FILE_PARSING_QUEUE = 'file_parsing_queue'
    
    def __init__(self):
        """Initialize Redis connection"""
        try:
            self.client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
                decode_responses=False
            )
            # Test connection
            self.client.ping()
            logger.info(f"Redis connected: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    def add_file_to_queue(self, file_id: str, metadata: Optional[Dict] = None) -> str:
        """
        Add a file to the parsing queue
        
        Args:
            file_id: MongoDB file ID
            metadata: Optional additional data (e.g., filename, priority)
        
        Returns:
            Message ID in Redis
        """
        data = {'file_id': file_id}
        if metadata:
            # Convert all values to strings to avoid Redis type errors
            for key, value in metadata.items():
                if value is None:
                    data[key] = ''
                elif isinstance(value, bool):
                    data[key] = str(value).lower()  # 'true' or 'false'
                elif isinstance(value, (int, float)):
                    data[key] = str(value)
                elif isinstance(value, str):
                    data[key] = value
                else:
                    # For complex types, convert to string
                    data[key] = str(value)
        
        try:
            msg_id = self.client.xadd(self.FILE_PARSING_QUEUE, data)
            logger.info(f"Added file {file_id} to parsing queue (msg_id: {msg_id})")
            return msg_id.decode('utf-8') if isinstance(msg_id, bytes) else msg_id
        except Exception as e:
            logger.error(f"Failed to add file {file_id} to queue: {e}")
            raise
    
    def get_queue_length(self) -> int:
        """Get number of pending messages in queue"""
        try:
            return self.client.xlen(self.FILE_PARSING_QUEUE)
        except:
            return 0
    
    def health_check(self) -> bool:
        """Check if Redis is connected"""
        try:
            return self.client.ping()
        except:
            return False


# Global instance
_redis_client: Optional[RedisQueueClient] = None


def get_redis_client() -> RedisQueueClient:
    """Get singleton Redis client"""
    global _redis_client
    if _redis_client is None:
        _redis_client = RedisQueueClient()
    return _redis_client


def init_redis():
    """Initialize Redis connection on startup"""
    try:
        client = get_redis_client()
        if client.health_check():
            logger.info("Redis client initialized successfully")
        else:
            logger.warning("Redis health check failed")
    except Exception as e:
        logger.error(f"Failed to initialize Redis: {e}")
        # Don't fail the application, just log the error

