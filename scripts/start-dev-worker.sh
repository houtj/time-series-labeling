#!/bin/bash
# Start development worker
# Uses dev Redis (localhost:6380) and MongoDB (localhost:27018)

cd hill_workers

echo "Starting development worker..."
echo "  MongoDB: localhost:27018"
echo "  Redis: localhost:6380"
echo ""

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Start the worker
python -m workers.file_parser_worker
