#!/bin/bash
# Start development backend server
# Runs on port 8001 (Prod uses 8000)

cd hill_backend

echo "Starting development backend on http://localhost:8001"
echo "  MongoDB: localhost:27018"
echo "  Redis: localhost:6380"
echo ""

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Start the backend
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
