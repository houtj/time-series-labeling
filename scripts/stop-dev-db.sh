#!/bin/bash
# Stop development databases (MongoDB and Redis)

echo "Stopping development databases..."
docker compose -f docker-compose.dev.yml down

echo "Development databases stopped!"
