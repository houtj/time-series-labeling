#!/bin/bash
# Start development frontend
# Runs on port 4201 (Prod uses 4200)
# Connects to dev backend at http://localhost:8001

cd hill_frontend

echo "Starting development frontend on http://localhost:4201"
echo "  Backend API: http://localhost:8001"
echo ""

# Start the Angular dev server
npm start
