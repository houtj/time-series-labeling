# Hill Workers V1.5

File parsing worker service using Redis Streams for task distribution.

> **For development setup and contribution guidelines**, see [README.dev.md](../README.dev.md) in the project root.

## Architecture

```
hill_workers_v1.5/
├── config.py              # Configuration from environment variables
├── database.py            # MongoDB connection
├── redis_client.py        # Redis Streams client
└── workers/
    └── file_parser.py     # File parsing worker
```

## Features

- ✅ **Redis Streams** - Push-based task distribution (no polling)
- ✅ **Structured Logging** - Comprehensive logging with timestamps and levels
- ✅ **Error Handling** - Robust error handling with database status updates
- ✅ **Scalability** - Multiple workers can process tasks in parallel
- ✅ **Modular Design** - Easy to add new worker types

## How It Works

### File Parsing Flow

1. Backend uploads a file and adds task to Redis queue:
   ```python
   redis.xadd('file_parsing_queue', {'file_id': '...'})
   ```

2. Worker consumes task from Redis:
   - Reads from Redis Streams (blocking)
   - Processes file according to template
   - Saves JSON output
   - Updates database status
   - Acknowledges message

3. Multiple workers can run in parallel:
   - Tasks are distributed among workers
   - No duplicate processing
   - If a worker crashes, another picks up the task

## Requirements

- Python 3.11+
- MongoDB
- Redis

## Setup

### 1. Install Dependencies

Using uv (recommended):
```bash
uv sync
```

Or using pip:
```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env` and adjust settings:
```bash
cp .env .env.local
```

Edit `.env.local`:
```bash
MONGODB_URL=mongodb://root:example@localhost:27017/
REDIS_HOST=localhost
REDIS_PORT=6379
DATA_FOLDER_PATH=./data_folder
WORKER_NAME=file-parser-1
LOG_LEVEL=INFO
```

### 3. Start Redis

Using Docker:
```bash
docker run -d -p 6379:6379 redis:7-alpine
```

Or use docker-compose (see project root).

## Running the Worker

### Development

```bash
# Using uv
uv run python -m workers.file_parser

# Using Python directly
python -m workers.file_parser
```

### Production (Docker)

```bash
docker-compose up worker
```

### Multiple Workers

Scale horizontally by running multiple instances:
```bash
# Terminal 1
WORKER_NAME=file-parser-1 uv run python -m workers.file_parser

# Terminal 2
WORKER_NAME=file-parser-2 uv run python -m workers.file_parser

# Terminal 3
WORKER_NAME=file-parser-3 uv run python -m workers.file_parser
```

All workers will consume from the same queue without duplicating work.

## Logging

Logs are written to both console and file (`worker.log` by default).

### Log Levels

- `DEBUG` - Detailed debugging information
- `INFO` - General informational messages
- `WARNING` - Warning messages
- `ERROR` - Error messages with stack traces
- `CRITICAL` - Critical errors

### Example Log Output

```
2025-10-01 14:23:45 - workers.file_parser - INFO - File Parser Worker started
2025-10-01 14:23:45 - workers.file_parser - INFO - Redis connection established
2025-10-01 14:23:50 - workers.file_parser - INFO - Processing message 1696165430000-0 for file 653abc123def456
2025-10-01 14:23:50 - workers.file_parser - INFO - Parsing file: sensor_data.csv
2025-10-01 14:23:51 - workers.file_parser - INFO - Saved JSON to project1/file1/sensor_data.json
2025-10-01 14:23:51 - workers.file_parser - INFO - Successfully processed file: sensor_data.csv
```

## Configuration

All settings are configured via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `MONGODB_URL` | `mongodb://root:example@localhost:27017/` | MongoDB connection URL |
| `REDIS_HOST` | `localhost` | Redis host |
| `REDIS_PORT` | `6379` | Redis port |
| `REDIS_PASSWORD` | (empty) | Redis password |
| `DATA_FOLDER_PATH` | `./data_folder` | Path to data files |
| `WORKER_NAME` | `file-parser-1` | Unique worker identifier |
| `BATCH_SIZE` | `10` | Max messages to process at once |
| `BLOCK_TIME_MS` | `5000` | Redis blocking timeout (ms) |
| `LOG_LEVEL` | `INFO` | Logging level |
| `LOG_FILE` | `worker.log` | Log file path |

## Adding New Workers

To add a new worker type (e.g., ML training):

1. Create `workers/ml_training.py`:
   ```python
   """ML Training Worker"""
   import sys
   from pathlib import Path
   sys.path.insert(0, str(Path(__file__).parent.parent))
   
   from config import settings
   from database import get_db
   from redis_client import get_redis_client
   
   class MLTrainingWorker:
       def run(self):
           # Your logic here
           pass
   
   if __name__ == "__main__":
       worker = MLTrainingWorker()
       worker.run()
   ```

2. Run the new worker:
   ```bash
   python -m workers.ml_training
   ```

## Troubleshooting

### Worker not processing files

1. Check Redis connection:
   ```bash
   redis-cli ping
   # Should return PONG
   ```

2. Check queue length:
   ```bash
   redis-cli XLEN file_parsing_queue
   ```

3. Check worker logs:
   ```bash
   tail -f worker.log
   ```

### Files stuck in "parsing start" status

- Worker may have crashed mid-processing
- Check pending messages:
  ```bash
  redis-cli XPENDING file_parsing_queue file_parsers
  ```
- Restart worker to pick up pending tasks

## Development

### Project Structure

- `config.py` - Centralized configuration
- `database.py` - MongoDB connection management
- `redis_client.py` - Redis Streams abstraction
- `workers/file_parser.py` - File parsing worker implementation

### Code Style

- Follow PEP 8
- Use type hints where appropriate
- Add docstrings to functions and classes
- Use structured logging (not print statements)

## License

Same as Hill TS project.

