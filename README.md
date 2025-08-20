# Hill Sequence - Time Series Labeling Tool

A comprehensive time-series labeling tool built with Angular frontend, FastAPI backend, Python workers, and MongoDB database.

## Architecture

The application consists of four main components:

- **Frontend (Angular)**: User interface for time-series visualization and labeling
- **Backend (FastAPI)**: REST API for data management and file operations
- **Worker (Python)**: Background service for parsing and processing time-series files
- **Database (MongoDB)**: Persistent storage for application data

## Quick Start with Docker

### Option 1: Using Published Images (Recommended)

For the fastest setup using our published Docker images:

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

See [QUICK_START.md](QUICK_START.md) for detailed instructions.

### Option 2: Build from Source

#### Prerequisites

- Docker and Docker Compose installed
- At least 4GB of available RAM
- 10GB of available disk space

#### 1. Clone the Repository

```bash
git clone <repository-url>
cd hill_sequence
```

### 2. Configure Environment Variables

Copy the environment template and customize as needed:

```bash
cp env.example .env
```

Edit `.env` file to configure:
- MongoDB credentials
- Port mappings
- Worker replicas
- **Persistent data paths** (see section below)

### 3. Start the Application

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Start with MongoDB Express (optional)
docker-compose --profile tools up -d
```

### 4. Access the Application

- **Frontend**: http://localhost:4200 (includes API proxy to backend)
- **MongoDB Express**: http://localhost:8081 (if enabled, for database administration)

## Docker Services

### Frontend (Port 4200)
- Angular application served with nginx
- Handles user interface and API communication
- **Includes nginx proxy** for API requests to backend
- Configured for production deployment

### Backend (Internal)
- FastAPI application with CORS enabled
- Handles file uploads, database operations, and API requests
- Uses uv for dependency management
- **Not externally exposed** - accessible via nginx proxy at `/api`

### Worker
- Background service for file parsing
- Processes Excel, CSV, and other time-series files
- Automatically scales based on workload

### MongoDB (Internal)
- Persistent database storage
- Initialized with required collections and indexes
- **Not externally exposed** - only accessible via internal Docker network

### MongoDB Express (Port 8081, Optional)
- Web-based MongoDB administration interface
- Accessible via `--profile tools` flag

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MONGO_ROOT_USERNAME` | root | MongoDB root username |
| `MONGO_ROOT_PASSWORD` | example | MongoDB root password |
| `MONGO_DATABASE` | hill_ts | Database name |
| `FRONTEND_PORT` | 4200 | Frontend port |
| `WORKER_REPLICAS` | 1 | Number of worker instances |

### Volumes

- `mongodb_data`: Persistent MongoDB data
- `app_data`: Application file storage

### Persistent Storage Configuration

The application uses bind mounts to persist data on the host system. You can configure the paths in your `.env` file:

```bash
# Persistent Data Paths
MONGODB_DATA_PATH=./mongodb_data    # MongoDB database files
APP_DATA_PATH=./app_data            # Application uploaded files
```

**Setup persistent storage:**

```bash
# Run the setup script (recommended)
./setup-persistent-storage.sh

# Or manually create directories
mkdir -p ./mongodb_data ./app_data
chmod 755 ./mongodb_data ./app_data
```

**Custom paths example:**
```bash
# In your .env file
MONGODB_DATA_PATH=/opt/hill_sequence/mongodb
APP_DATA_PATH=/opt/hill_sequence/app_data
```

**Important notes:**
- Use absolute paths for production deployments
- Ensure the directories have proper permissions (755)
- The directories will be created automatically if they don't exist
- Data persists across container restarts and updates

## Development

### Building Individual Services

```bash
# Build frontend
docker-compose build frontend

# Build backend
docker-compose build backend

# Build worker
docker-compose build worker
```

### Running in Development Mode

```bash
# Start only required services
docker-compose up mongodb backend worker

# Run frontend locally
cd hill_frontend
npm install
ng serve
```

### Viewing Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f worker
```

## Production Deployment

### 1. Configure Production Environment

```bash
# Set production environment variables
export MONGO_ROOT_PASSWORD=your_secure_password
export MONGO_EXPRESS_PASSWORD=your_admin_password
```

### 2. Deploy with Docker Compose

```bash
# Build and start all services
docker-compose -f docker-compose.yml up -d --build

# Scale workers if needed
docker-compose up -d --scale worker=3
```

### 3. Set Up Reverse Proxy (Optional)

For production, consider using nginx or traefik as a reverse proxy:

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:4200;
    }
    
    location /api {
        proxy_pass http://localhost:8000;
    }
}
```

## Troubleshooting

### Common Issues

1. **Port Conflicts**
   ```bash
   # Check port usage
   netstat -tulpn | grep :4200
   
   # Change ports in .env file
   FRONTEND_PORT=4201
   ```

2. **MongoDB Connection Issues**
   ```bash
   # Check MongoDB logs
   docker-compose logs mongodb
   
   # Verify network connectivity
   docker-compose exec backend ping mongodb
   ```

3. **Worker Not Processing Files**
   ```bash
   # Check worker logs
   docker-compose logs worker
   
   # Verify MongoDB connection
   docker-compose exec worker python -c "import pymongo; print(pymongo.MongoClient('mongodb://root:example@mongodb:27017/').server_info())"
   ```

### Health Checks

All services include health checks. Monitor with:

```bash
docker-compose ps
```

### Data Backup

```bash
# Backup MongoDB data
docker-compose exec mongodb mongodump --out /backup

# Backup application data (using bind mount paths)
tar czf mongodb_backup_$(date +%Y%m%d_%H%M%S).tar.gz -C ${MONGODB_DATA_PATH:-./mongodb_data} .
tar czf app_data_backup_$(date +%Y%m%d_%H%M%S).tar.gz -C ${APP_DATA_PATH:-./app_data} .

# Or backup using Docker volumes
docker run --rm -v hill_sequence_app_data:/data -v $(pwd):/backup alpine tar czf /backup/app_data_backup.tar.gz -C /data .
```

## Security Considerations

1. **Change Default Passwords**: Update MongoDB and MongoDB Express passwords
2. **Network Security**: Use Docker networks for service isolation
3. **Volume Permissions**: Ensure proper file permissions on mounted volumes
4. **HTTPS**: Use reverse proxy with SSL certificates for production

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review service logs
3. Verify configuration settings
4. Check Docker and Docker Compose versions

## License

[Add your license information here]
