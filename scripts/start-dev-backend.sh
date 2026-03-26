#!/bin/bash
# Start development backend server
# Runs on port 8001 (Prod uses 8000)

# Set dev environment variables (must be before cd)
export REDIS_HOST=localhost
export REDIS_PORT=6380
export MONGODB_URL=mongodb://root:example@localhost:27018/
export DATA_FOLDER_PATH="$(pwd)/app_data"

cd hill_backend

echo "Starting development backend on http://localhost:8001"
echo "  MongoDB: localhost:27018"
echo "  Redis: localhost:6380"
echo "  Data folder: $DATA_FOLDER_PATH"
echo ""

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Start the backend
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
