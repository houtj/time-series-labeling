# Hill Sequence - Quick Start Guide

This guide shows you how to quickly deploy Hill Sequence using the published Docker images.

## Prerequisites

- Docker and Docker Compose installed
- At least 4GB of available RAM
- 10GB of available disk space

## Quick Deployment

### 1. Create Project Directory
```bash
mkdir hill-sequence
cd hill-sequence
```

### 2. Download Configuration Files
```bash
# Download docker-compose file
curl -O https://raw.githubusercontent.com/your-username/hill-sequence/main/docker-compose.prod.yml

# Download environment template
curl -O https://raw.githubusercontent.com/your-username/hill-sequence/main/env.example

# Download MongoDB initialization script
curl -O https://raw.githubusercontent.com/your-username/hill-sequence/main/init-mongo.js
```

### 3. Configure Environment
```bash
# Copy and edit environment file
cp env.example .env

# Edit the .env file with your settings
nano .env
```

**Required environment variables:**
```bash
# Your Docker Hub username
DOCKER_USERNAME=your-dockerhub-username

# Version to use (latest, v1.0.0, etc.)
VERSION=latest

# MongoDB credentials (change these!)
MONGO_ROOT_USERNAME=admin
MONGO_ROOT_PASSWORD=your_secure_password

# Optional: Custom data paths
MONGODB_DATA_PATH=./mongodb_data
APP_DATA_PATH=./app_data
```

### 4. Start the Application
```bash
# Start all services
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

### 5. Access the Application
- **Frontend**: http://localhost:4200
- **Backend API**: http://localhost:8000
- **MongoDB Express**: http://localhost:8081 (optional)

## One-Line Deployment

For the fastest setup, you can use this single command:

```bash
# Create directory and download files
mkdir hill-sequence && cd hill-sequence && \
curl -O https://raw.githubusercontent.com/your-username/hill-sequence/main/docker-compose.prod.yml && \
curl -O https://raw.githubusercontent.com/your-username/hill-sequence/main/env.example && \
curl -O https://raw.githubusercontent.com/your-username/hill-sequence/main/init-mongo.js && \
cp env.example .env && \
echo "DOCKER_USERNAME=your-dockerhub-username" >> .env && \
echo "VERSION=latest" >> .env && \
docker-compose -f docker-compose.prod.yml up -d
```

## Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DOCKER_USERNAME` | your-username | Your Docker Hub username |
| `VERSION` | latest | Image version to use |
| `MONGO_ROOT_USERNAME` | root | MongoDB root username |
| `MONGO_ROOT_PASSWORD` | example | MongoDB root password |
| `MONGO_DATABASE` | hill_ts | Database name |
| `MONGO_PORT` | 27017 | MongoDB port |
| `BACKEND_PORT` | 8000 | Backend API port |
| `FRONTEND_PORT` | 4200 | Frontend port |
| `WORKER_REPLICAS` | 1 | Number of worker instances |
| `MONGODB_DATA_PATH` | ./mongodb_data | MongoDB data directory |
| `APP_DATA_PATH` | ./app_data | Application data directory |

### Custom Data Paths

For production deployments, use absolute paths:

```bash
# In your .env file
MONGODB_DATA_PATH=/opt/hill_sequence/mongodb
APP_DATA_PATH=/opt/hill_sequence/app_data
```

### Scaling Workers

To scale the worker service:

```bash
# Scale to 3 workers
docker-compose -f docker-compose.prod.yml up -d --scale worker=3
```

## Management Commands

### View Status
```bash
docker-compose -f docker-compose.prod.yml ps
```

### View Logs
```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f backend
```

### Stop Services
```bash
docker-compose -f docker-compose.prod.yml down
```

### Update to New Version
```bash
# Update environment variable
echo "VERSION=v1.1.0" > .env

# Pull and restart
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

## Troubleshooting

### Port Conflicts
If you get port conflicts, change the ports in your `.env` file:
```bash
FRONTEND_PORT=4201
BACKEND_PORT=8001
MONGO_PORT=27018
```

### Permission Issues
If you get permission errors with data directories:
```bash
# Create directories with proper permissions
mkdir -p mongodb_data app_data
chmod 755 mongodb_data app_data
```

### Memory Issues
If the application is slow or crashes:
```bash
# Increase Docker memory limit to 4GB or more
# In Docker Desktop: Settings > Resources > Memory
```

### Database Connection Issues
Check if MongoDB is running:
```bash
docker-compose -f docker-compose.prod.yml logs mongodb
```

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review service logs
3. Check the [GitHub repository](https://github.com/your-username/hill-sequence)
4. Open an issue on GitHub

## License

[Add your license information here]
