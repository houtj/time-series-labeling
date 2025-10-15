# Redis Integration - Backend V1.5

## Overview

The backend has been updated to use Redis Streams for task distribution to workers instead of the old polling-based approach.

## Changes Made

### 1. New File: `redis_client.py`

Added Redis client for publishing file parsing tasks to the queue:

```python
# Main functions:
- add_file_to_queue(file_id, metadata)  # Add task to Redis
- get_queue_length()                     # Get pending tasks count
- health_check()                         # Check Redis connection
```

### 2. Updated: `config.py`

Added Redis configuration settings:

```python
# Redis (for task queue)
REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")
```

### 3. Updated: `main.py`

Added Redis initialization on startup:

```python
from redis_client import init_redis

# Initialize Redis on startup
init_redis()
```

### 4. Updated: `routes/files.py`

Modified file upload and reparse endpoints to use Redis queue:

#### File Upload (POST /files)

**Before:**
```python
fileInfo['parsing'] = 'parsing start'
db['files'].update_one({'_id': newFileId}, {'$set': fileInfo})
```

**After:**
```python
fileInfo['parsing'] = 'queued'
db['files'].update_one({'_id': newFileId}, {'$set': fileInfo})

# Add to Redis queue
redis = get_redis_client()
redis.add_file_to_queue(
    file_id=str(newFileId),
    metadata={'filename': file.filename, 'folder_id': folderId}
)
```

#### Reparse Files (PUT /files/reparse)

**Before:**
```python
db['files'].update_many(
    {'_id': {'$in': [ObjectId(id) for id in files_id]}}, 
    {'$set': {'parsing': 'parsing start'}}
)
```

**After:**
```python
db['files'].update_many(
    {'_id': {'$in': [ObjectId(id) for id in files_id]}}, 
    {'$set': {'parsing': 'queued'}}
)

# Add all files to Redis queue
redis = get_redis_client()
for file_id in files_id:
    redis.add_file_to_queue(
        file_id=file_id,
        metadata={'reparse': True, 'folder_id': request.folderId}
    )
```

## File Status Flow

### Old Flow (Polling-based)
```
uploading → parsing start → parsed/error
            ↑
            └── Worker polls database every 30s
```

### New Flow (Redis Streams)
```
uploading → queued → parsed/error
            ↓
            └── Added to Redis queue → Worker consumes instantly
```

## Status Values

| Status | Meaning |
|--------|---------|
| `uploading` | File is being uploaded to server |
| `queued` | File has been added to Redis queue, waiting for worker |
| `parsed` | File has been successfully parsed by worker |
| `error: <msg>` | File parsing failed with error message |

## Error Handling

The backend includes fallback logic if Redis is unavailable:

```python
try:
    redis = get_redis_client()
    redis.add_file_to_queue(str(newFileId), ...)
except Exception as e:
    logger.error(f"Failed to add file to Redis queue: {e}")
    # Fall back to old method
    db['files'].update_one({'_id': newFileId}, {'$set': {'parsing': 'parsing start'}})
```

This ensures the system continues to work even if Redis is down (workers can still poll for 'parsing start' status).

## Environment Variables

Add to your `.env` file:

```bash
# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
```

For Docker:
```bash
# In docker-compose.yml
REDIS_HOST=redis
REDIS_PORT=6379
```

## Benefits

1. **Instant Processing** - No 30-second polling delay
2. **Scalability** - Multiple workers can consume from same queue
3. **Reliability** - Messages are persisted and acknowledged
4. **Monitoring** - Can check queue length, pending tasks, etc.
5. **Decoupling** - Backend and workers are truly independent

## Integration with Workers

The worker (`hill_workers_v1.5`) consumes from the same Redis queue:

1. Backend adds task: `redis.xadd('file_parsing_queue', {'file_id': '...'})`
2. Worker reads task: `redis.xreadgroup('file_parsers', 'worker-1', ...)`
3. Worker processes file
4. Worker updates database: `parsing: 'parsed'`
5. Worker acknowledges: `redis.xack(...)`

## Testing

### 1. Check Redis Connection

```python
from redis_client import get_redis_client

redis = get_redis_client()
print(redis.health_check())  # Should return True
```

### 2. Check Queue Length

```python
from redis_client import get_redis_client

redis = get_redis_client()
print(redis.get_queue_length())  # Number of pending tasks
```

### 3. Manual Task Addition

```python
from redis_client import get_redis_client

redis = get_redis_client()
msg_id = redis.add_file_to_queue('653abc123def456')
print(f"Added task: {msg_id}")
```

## Troubleshooting

### Redis Connection Failed

**Error:** `Failed to connect to Redis: [Errno 111] Connection refused`

**Solution:**
1. Make sure Redis is running:
   ```bash
   docker run -d -p 6379:6379 redis:7-alpine
   ```
2. Check Redis host/port in `.env`
3. Check Redis logs: `docker logs hill-redis`

### Tasks Not Being Processed

1. Check queue length:
   ```bash
   redis-cli XLEN file_parsing_queue
   ```

2. Check if worker is running:
   ```bash
   cd hill_workers_v1.5
   uv run python -m workers.file_parser
   ```

3. Check backend logs for errors

### Files Stuck in 'queued' Status

1. Worker may have crashed - restart worker
2. Check Redis queue:
   ```bash
   redis-cli XPENDING file_parsing_queue file_parsers
   ```
3. Files will be picked up by next available worker

## Migration Notes

### Backward Compatibility

The system maintains backward compatibility:
- If Redis fails, files are marked with old status `'parsing start'`
- Old workers can still poll for `'parsing start'` status
- New workers consume from Redis queue

### Gradual Migration

You can run both systems in parallel:
1. Old workers poll for `'parsing start'`
2. New workers consume from Redis queue
3. Backend sends to both (fallback ensures this)

Eventually, remove old workers once Redis is stable.

## Future Enhancements

Potential improvements (not implemented yet):

1. **Priority Queues** - Different priorities for different files
2. **Dead Letter Queue** - Handle repeatedly failing tasks
3. **Task Retry** - Automatic retry with exponential backoff
4. **Monitoring Dashboard** - Real-time queue statistics
5. **Multiple Queues** - Separate queues for parsing, ML, exports, etc.

## Summary

The Redis integration transforms the backend from a polling-based system to a modern, event-driven architecture:

- ✅ **Added** `redis_client.py` for queue management
- ✅ **Updated** `config.py` with Redis settings
- ✅ **Updated** `main.py` to initialize Redis
- ✅ **Updated** `routes/files.py` to use Redis queue
- ✅ **Changed** file status from `'parsing start'` to `'queued'`
- ✅ **Added** fallback logic for Redis failures
- ✅ **Maintained** backward compatibility

The backend is now ready to work with the new `hill_workers_v1.5` workers! 🎉

