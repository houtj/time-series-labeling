# Hill Sequence - Developer Guide

This guide is for developers and contributors working on the Hill Sequence project.

## Table of Contents

- [Dev/Prod Environment Isolation](#devprod-environment-isolation)
- [Local Development Setup](#local-development-setup)
- [Building from Source](#building-from-source)
- [CI/CD Pipeline Setup](#cicd-pipeline-setup)
- [Release Process](#release-process)
- [Contributing](#contributing)

## Dev/Prod Environment Isolation

The development and production environments are completely isolated to prevent interference:

### Port Allocation

| Service | Production Port | Development Port |
|---------|----------------|------------------|
| Frontend | 4200 | 4201 |
| Backend | 8000 | 8001 |
| MongoDB | 27017 (not exposed) | 27018 |
| Redis | 6379 (not exposed) | 6380 |

### Data Isolation

- **Production**: Located in `~/projects/hill-app/`
  - All services run in Docker containers
  - MongoDB and Redis are NOT exposed to host (internal network only)
  - Data stored in `~/projects/hill-app/app_data`

- **Development**: Located in `~/projects/hill_dev/`
  - MongoDB and Redis run in Docker containers (different ports)
  - Backend, Frontend, Worker run in terminals for hot-reload
  - Data stored in `~/projects/hill_dev/dev_data`

### Benefits of Isolation

- No port conflicts between dev and prod
- Dev changes don't affect production data
- Dev and prod workers use separate Redis queues
- Safe to test breaking changes in development
- Can run both environments simultaneously

## Local Development Setup

### Prerequisites

- Docker and Docker Compose
- Node.js 20+ (for frontend development)
- Python 3.11+ (for backend development)
- Git

### Development Environment

The project uses `docker compose.dev.yml` for local development, which provides isolated MongoDB (port 27018) and Redis (port 6380). You run the application services (backend, frontend, worker) locally on your machine for faster development iteration.

### Quick Start with Scripts

We provide convenient startup scripts:

```bash
# 1. Start development databases (MongoDB + Redis)
./scripts/start-dev-db.sh

# 2. (Optional) Sync production data to dev for realistic testing
./scripts/sync-prod-to-dev.sh

# 3. In separate terminals, start each service:
./scripts/start-dev-backend.sh   # Runs on http://localhost:8001
./scripts/start-dev-worker.sh    # Connects to dev Redis queue
./scripts/start-dev-frontend.sh  # Runs on http://localhost:4201

# Stop databases when done
./scripts/stop-dev-db.sh
```

**Note:** The sync script (`sync-prod-to-dev.sh`) copies all production data including:
- Application data (uploaded files, parsed JSON)
- MongoDB database (complete database copy)
- Redis data (cleared and started fresh)

This is useful for testing with real production data in a safe isolated environment.

### Manual Setup (Alternative)

If you prefer manual setup:

### 1. Clone the Repository

```bash
git clone <repository-url>
cd time-series-labeling
```

### 2. Start Development Dependencies

```bash
# Start MongoDB (port 27018) and Redis (port 6380)
docker compose -f docker compose.dev.yml up -d

# Verify services are running
docker compose -f docker compose.dev.yml ps
```

### 3. Backend Development

```bash
cd hill_backend

# Install dependencies using uv
pip install uv
uv sync

# Create .env file (optional, for local config)
cp ../.env.example .env
# Edit .env with your Azure OpenAI credentials

# Run the backend (dev uses port 8001, prod uses 8000)
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

Backend will be available at: http://localhost:8001

### 4. Frontend Development

```bash
cd hill_frontend

# Install dependencies
npm install

# Run development server (dev uses port 4201, prod uses 4200)
npm start
# or
ng serve
```

Frontend will be available at: http://localhost:4201

### 5. Worker Development

```bash
cd hill_workers

# Install dependencies
pip install uv
uv sync

# Run the worker
uv run python -m workers.file_parser
```

### Development Workflow

1. Make your changes in the codebase
2. Test locally with hot-reload enabled
3. Commit your changes
4. Push to your branch
5. Create a Pull Request

## Building from Source

### Build All Services with Docker

```bash
# Build all services
docker compose -f docker compose.prod.yml build

# Build specific service
docker build -t hill-backend ./hill_backend
docker build -t hill-frontend ./hill_frontend
docker build -t hill-worker ./hill_workers
```

### Test Production Build Locally

```bash
# Create .env file with production settings
cp env.example .env
# Edit .env with your credentials

# Build and run
docker compose -f docker compose.prod.yml build
docker compose -f docker compose.prod.yml up -d

# Test the application
open http://localhost:4200

# Stop services
docker compose -f docker compose.prod.yml down
```

## CI/CD Pipeline Setup

The project uses GitHub Actions for automated builds and releases. When you push a tag, the pipeline automatically builds Docker images and publishes them to DockerHub.

### Required Accounts

1. **DockerHub Account**: For hosting Docker images
2. **GitHub Account**: For repository and CI/CD

### Setup Instructions

#### 1. DockerHub Setup

1. Go to [DockerHub](https://hub.docker.com)
2. Sign in with username: `houtj1990` (or your username)
3. Navigate to **Account Settings** → **Security**
4. Click **New Access Token**
   - Token description: `GitHub Actions`
   - Permissions: `Read & Write`
5. Click **Generate**
6. **Copy the token** (it will only be shown once)

#### 2. GitHub Repository Secrets

1. Go to your GitHub repository
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add the following secrets:

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `DOCKER_USERNAME` | `houtj1990` | Your DockerHub username |
| `DOCKER_TOKEN` | `[your-token]` | DockerHub access token from step 1 |

#### 3. Verify Workflow Configuration

The workflow file is located at `.github/workflows/production.yml`. It's already configured and will:
- Trigger on semantic version tags (v1.0.0, v2.1.3, etc.)
- Build three Docker images (backend, frontend, worker)
- Push to DockerHub with version tag and "latest"
- Create a GitHub Release with deployment instructions

## Release Process

### Creating a New Release

1. **Ensure all changes are committed and pushed**:
   ```bash
   git add .
   git commit -m "Release v1.2.0: Add new features"
   git push origin main
   ```

2. **Create and push a version tag**:
   ```bash
   # Create an annotated tag (recommended)
   git tag -a v1.2.0 -m "Release v1.2.0: Feature description"
   
   # Push the tag to trigger the pipeline
   git push origin v1.2.0
   ```

3. **Monitor the build**:
   - Go to your GitHub repository
   - Click **Actions** tab
   - Watch the "Production Release" workflow run
   - Build takes approximately 5-10 minutes

4. **Verify the release**:
   - Check [DockerHub](https://hub.docker.com/u/houtj1990) for new images
   - Check GitHub **Releases** for the new release
   - Test deployment using the published images

### Version Tag Format

Use semantic versioning: `v[major].[minor].[patch]`

Examples:
- `v1.0.0` - Major release
- `v1.2.0` - Minor release (new features)
- `v1.2.1` - Patch release (bug fixes)

### What Happens During Release

1. **Tag Validation**: Verifies tag follows semantic versioning
2. **Build Images**: Builds backend, frontend, and worker in parallel
3. **Push to DockerHub**: Pushes images with version tag and "latest"
4. **Create GitHub Release**: Creates a release with deployment instructions

### Release Artifacts

After a successful release, the following images are available on DockerHub:

- `houtj1990/hill-sequence-backend:v1.2.0`
- `houtj1990/hill-sequence-backend:latest`
- `houtj1990/hill-sequence-frontend:v1.2.0`
- `houtj1990/hill-sequence-frontend:latest`
- `houtj1990/hill-sequence-worker:v1.2.0`
- `houtj1990/hill-sequence-worker:latest`

## Project Structure

```
time-series-labeling/
├── .github/
│   └── workflows/
│       └── production.yml       # CI/CD pipeline
├── hill_backend/
│   ├── agents/                  # AI agents
│   ├── routes/                  # API routes
│   ├── ws_handlers/             # WebSocket handlers
│   ├── Dockerfile               # Backend container
│   ├── main.py                  # FastAPI application
│   └── pyproject.toml           # Python dependencies
├── hill_frontend/
│   ├── src/                     # Angular source
│   ├── Dockerfile               # Frontend container
│   ├── nginx.conf               # Production nginx config
│   └── package.json             # Node dependencies
├── hill_workers/
│   ├── workers/                 # Background workers
│   ├── Dockerfile               # Worker container
│   └── pyproject.toml           # Python dependencies
├── docker compose.dev.yml       # Development (MongoDB + Redis)
├── docker compose.prod.yml      # Production (all services)
├── env.example                  # Environment template
├── init-mongo.js                # MongoDB initialization
├── README.md                    # User documentation
└── README.dev.md                # Developer documentation (this file)
```

## Development Tips

### Backend Development

- Uses `uv` for fast dependency management
- FastAPI auto-reloads on file changes
- API docs available at: http://localhost:8000/docs
- Uses Redis Streams for task queuing

### Frontend Development

- Angular 17+ with standalone components
- Uses signals for state management
- Proxy configuration for API calls in development
- Build optimization for production

### Worker Development

- Consumes tasks from Redis queue
- Parses CSV and Excel files
- Updates MongoDB with parsed data
- Supports multiple concurrent workers

## Debugging

### Backend Debugging

```bash
# With breakpoints
uv run python -m debugpy --listen 5678 --wait-for-client -m uvicorn main:app --reload
```

### View Logs

```bash
# Development services
docker compose -f docker compose.dev.yml logs -f

# Production services
docker compose -f docker compose.prod.yml logs -f backend
```

### Database Access

```bash
# Connect to Dev MongoDB
docker compose -f docker compose.dev.yml exec mongodb mongosh -u root -p example

# Or use MongoDB Compass
# Dev connection string: mongodb://root:example@localhost:27018
# Prod connection string: mongodb://root:example@localhost:27017 (if exposed)
```

## Testing

### Backend Tests

```bash
cd hill_backend
uv run pytest
```

### Frontend Tests

```bash
cd hill_frontend
npm test
```

## Contributing

### Code Style

- **Python**: Follow PEP 8, use `black` for formatting
- **TypeScript**: Follow Angular style guide, use `prettier`
- **Commits**: Use conventional commits (feat:, fix:, docs:, etc.)

### Pull Request Process

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make your changes
3. Test locally
4. Commit with descriptive messages
5. Push and create a Pull Request
6. Request review from maintainers

### Release Checklist

Before creating a release tag:

- [ ] All tests pass
- [ ] Documentation is updated
- [ ] CHANGELOG is updated
- [ ] Version numbers are updated
- [ ] Local production build works
- [ ] Breaking changes are documented

## Troubleshooting Development Issues

### Docker Build Fails

```bash
# Clean Docker cache
docker system prune -a

# Rebuild without cache
docker compose -f docker compose.prod.yml build --no-cache
```

### Port Conflicts

Dev and prod environments use different ports to avoid conflicts:
- Frontend: Dev=4201, Prod=4200
- Backend: Dev=8001, Prod=8000
- MongoDB: Dev=27018, Prod=27017 (not exposed in new setup)
- Redis: Dev=6380, Prod=6379 (not exposed in new setup)

```bash
# Check what's using the port
lsof -i :8001  # Dev backend
lsof -i :4201  # Dev frontend
lsof -i :27018 # Dev MongoDB
lsof -i :6380  # Dev Redis

# Kill the process if needed
kill -9 <PID>
```

### Dependencies Out of Sync

```bash
# Backend
cd hill_backend
rm -rf .venv
uv sync

# Frontend
cd hill_frontend
rm -rf node_modules package-lock.json
npm install
```

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Angular Documentation](https://angular.io/docs)
- [Docker Documentation](https://docs.docker.com/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

## Support

For development questions:
- Check this documentation
- Review existing code and comments
- Check GitHub Issues and Pull Requests
- Contact the maintainers

