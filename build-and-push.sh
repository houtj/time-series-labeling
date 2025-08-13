#!/bin/bash

# Hill Sequence Docker Image Build and Push Script
# This script builds and pushes all Docker images to Docker Hub

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration
DOCKER_USERNAME=${DOCKER_USERNAME:-"your-dockerhub-username"}
IMAGE_PREFIX=${IMAGE_PREFIX:-"hill-sequence"}
VERSION=${VERSION:-"latest"}

# Check if Docker is logged in
if ! docker info | grep -q "Username"; then
    print_error "You are not logged in to Docker Hub. Please run: docker login"
    exit 1
fi

print_status "Building and pushing Hill Sequence Docker images..."
print_status "Docker Hub Username: $DOCKER_USERNAME"
print_status "Image Prefix: $IMAGE_PREFIX"
print_status "Version: $VERSION"

# Build and push Frontend
print_status "Building frontend image..."
docker build -t $DOCKER_USERNAME/$IMAGE_PREFIX-frontend:$VERSION ./hill_frontend
docker build -t $DOCKER_USERNAME/$IMAGE_PREFIX-frontend:latest ./hill_frontend

print_status "Pushing frontend image..."
docker push $DOCKER_USERNAME/$IMAGE_PREFIX-frontend:$VERSION
docker push $DOCKER_USERNAME/$IMAGE_PREFIX-frontend:latest

# Build and push Backend
print_status "Building backend image..."
docker build -t $DOCKER_USERNAME/$IMAGE_PREFIX-backend:$VERSION ./hill_backend
docker build -t $DOCKER_USERNAME/$IMAGE_PREFIX-backend:latest ./hill_backend

print_status "Pushing backend image..."
docker push $DOCKER_USERNAME/$IMAGE_PREFIX-backend:$VERSION
docker push $DOCKER_USERNAME/$IMAGE_PREFIX-backend:latest

# Build and push Worker
print_status "Building worker image..."
docker build -t $DOCKER_USERNAME/$IMAGE_PREFIX-worker:$VERSION ./hill_workers
docker build -t $DOCKER_USERNAME/$IMAGE_PREFIX-worker:latest ./hill_workers

print_status "Pushing worker image..."
docker push $DOCKER_USERNAME/$IMAGE_PREFIX-worker:$VERSION
docker push $DOCKER_USERNAME/$IMAGE_PREFIX-worker:latest

print_status "All images built and pushed successfully!"
print_status ""
print_status "Images published:"
print_status "  - $DOCKER_USERNAME/$IMAGE_PREFIX-frontend:$VERSION"
print_status "  - $DOCKER_USERNAME/$IMAGE_PREFIX-backend:$VERSION"
print_status "  - $DOCKER_USERNAME/$IMAGE_PREFIX-worker:$VERSION"
print_status ""
print_status "Next steps:"
print_status "1. Update docker-compose.yml to use published images"
print_status "2. Create a release on GitHub"
print_status "3. Update documentation"
