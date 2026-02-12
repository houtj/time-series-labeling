#!/bin/bash
# Start development databases (MongoDB and Redis)
# These run on different ports than production to ensure isolation

echo "Starting development databases..."
echo "  MongoDB: localhost:27018"
echo "  Redis: localhost:6380"
echo ""

docker compose -f docker-compose.dev.yml up -d

echo ""
echo "Development databases started!"
echo ""
echo "To stop: docker compose -f docker-compose.dev.yml down"
echo "To view logs: docker compose -f docker-compose.dev.yml logs -f"
