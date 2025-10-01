"""
Redis Client for Task Queue Management
Handles Redis Streams for task distribution
"""
import redis
import logging
from typing import Optional, List, Dict, Any
from config import settings

logger = logging.getLogger(__name__)

class RedisQueueClient:
    """Redis Streams client for task queue management"""
    
    # Queue names
    FILE_PARSING_QUEUE = 'file_parsing_queue'
    
    # Consumer group names
    PARSER_GROUP = 'file_parsers'
    
    def __init__(self):
        """Initialize Redis connection"""
        self.client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
            decode_responses=False  # Keep binary for xreadgroup
        )
        self._ensure_consumer_groups()
    
    def _ensure_consumer_groups(self):
        """Create consumer groups if they don't exist"""
        try:
            self.client.xgroup_create(
                self.FILE_PARSING_QUEUE,
                self.PARSER_GROUP,
                id='0',
                mkstream=True
            )
            logger.info(f"Created consumer group: {self.PARSER_GROUP}")
        except redis.exceptions.ResponseError as e:
            if "BUSYGROUP" in str(e):
                logger.debug(f"Consumer group already exists: {self.PARSER_GROUP}")
            else:
                raise
    
    def add_file_to_queue(self, file_id: str, metadata: Optional[Dict] = None) -> str:
        """
        Add a file to the parsing queue
        
        Args:
            file_id: MongoDB file ID
            metadata: Optional additional data
        
        Returns:
            Message ID in Redis
        """
        data = {'file_id': file_id}
        if metadata:
            data.update(metadata)
        
        msg_id = self.client.xadd(self.FILE_PARSING_QUEUE, data)
        logger.info(f"Added file {file_id} to queue (msg_id: {msg_id})")
        return msg_id
    
    def read_messages(
        self,
        consumer_name: str,
        count: int = 10,
        block_ms: int = 5000
    ) -> List[tuple]:
        """
        Read messages from queue (blocking)
        
        Args:
            consumer_name: Name of this consumer (e.g., 'worker-1')
            count: Max messages to read
            block_ms: Milliseconds to wait for messages
        
        Returns:
            List of (stream_name, [(msg_id, data), ...])
        """
        try:
            messages = self.client.xreadgroup(
                self.PARSER_GROUP,
                consumer_name,
                {self.FILE_PARSING_QUEUE: '>'},
                count=count,
                block=block_ms
            )
            return messages if messages else []
        except Exception as e:
            logger.error(f"Error reading from Redis: {e}")
            return []
    
    def acknowledge(self, message_id: str):
        """Acknowledge message as processed"""
        try:
            self.client.xack(self.FILE_PARSING_QUEUE, self.PARSER_GROUP, message_id)
            logger.debug(f"Acknowledged message: {message_id}")
        except Exception as e:
            logger.error(f"Error acknowledging message {message_id}: {e}")
    
    def get_queue_length(self) -> int:
        """Get number of pending messages in queue"""
        try:
            return self.client.xlen(self.FILE_PARSING_QUEUE)
        except:
            return 0
    
    def get_pending_count(self) -> int:
        """Get number of messages pending acknowledgment"""
        try:
            pending = self.client.xpending(self.FILE_PARSING_QUEUE, self.PARSER_GROUP)
            return pending['pending'] if pending else 0
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

