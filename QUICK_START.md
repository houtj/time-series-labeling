# Hill Sequence - Quick Start Guide

Get Hill Sequence running in under 5 minutes!

## What You'll Need

- Docker and Docker Compose installed
- 4GB+ RAM available
- Azure OpenAI API credentials ([Get them here](https://azure.microsoft.com/en-us/products/ai-services/openai-service))

## Quick Installation

### Step 1: Create Deployment Directory

```bash
mkdir hill-app && cd hill-app
```

### Step 2: Download Required Files

```bash
curl -O https://raw.githubusercontent.com/houtj/time-series-labeling/master/docker-compose.prod.yml
curl -O https://raw.githubusercontent.com/houtj/time-series-labeling/master/env.example
curl -O https://raw.githubusercontent.com/houtj/time-series-labeling/master/init-mongo.js
```

### Step 2.5: Create Data Directories

```bash
# Create directories for persistent data
mkdir -p mongodb_data app_data

# Verify you're in the right directory
ls -la
# You should see: docker-compose.prod.yml, env.example, init-mongo.js, mongodb_data/, app_data/
```

### Step 3: Configure Environment

```bash
# Copy template
cp env.example .env

# Edit configuration (use your favorite editor)
nano .env
# or
vim .env
```

**Required: Add your Azure OpenAI credentials**:

```bash
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
API_VERSION=2024-02-01
API_KEY=your-actual-api-key-here
API_ENDPOINT=https://your-resource.openai.azure.com/
```

**Optional: Change default password** (recommended for production):

```bash
MONGO_ROOT_PASSWORD=your-secure-password-here
```

### Step 4: Start the Application

**IMPORTANT**: Make sure you're in the `hill-app` directory before running docker-compose!

```bash
# Verify you're in the correct directory
pwd
# Should show: /path/to/hill-app

# Start the application
docker-compose -f docker-compose.prod.yml up -d
```

This will:
- Download Docker images (~2GB)
- Start all services (MongoDB, Redis, Backend, Worker, Frontend)
- Initialize the database
- Takes 2-3 minutes on first run

**Note**: Data will be stored in `./mongodb_data` and `./app_data` directories relative to where you run docker-compose.

### Step 5: Access the Application

Open your browser to: **http://localhost:4200**

## One-Line Installation

For the fastest setup, copy and paste this:

```bash
mkdir hill-app && cd hill-app && \
curl -O https://raw.githubusercontent.com/houtj/time-series-labeling/master/docker-compose.prod.yml && \
curl -O https://raw.githubusercontent.com/houtj/time-series-labeling/master/env.example && \
curl -O https://raw.githubusercontent.com/houtj/time-series-labeling/master/init-mongo.js && \
mkdir -p mongodb_data app_data && \
cp env.example .env && \
echo "✅ Files downloaded and directories created!" && \
echo "Next steps:" && \
echo "1. Edit .env with your OpenAI credentials" && \
echo "2. Run: docker-compose -f docker-compose.prod.yml up -d"
```

## Verify Installation

Check that all services are running:

```bash
docker-compose -f docker-compose.prod.yml ps
```

You should see 5 services running:
- ✅ hill-mongodb (healthy)
- ✅ hill-redis (healthy)
- ✅ hill-backend (healthy)
- ✅ hill-worker (healthy)
- ✅ hill-frontend (healthy)

## Common Issues

### Port 4200 Already in Use

Change the port in your `.env` file:

```bash
FRONTEND_PORT=4201
```

Restart the application:

```bash
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d
```

Access at: http://localhost:4201

### Services Not Starting

Check the logs:

```bash
docker-compose -f docker-compose.prod.yml logs
```

Common causes:
- Not enough RAM (need 4GB minimum)
- Docker not running
- Port conflicts

### AI Features Not Working

Verify your OpenAI credentials in `.env`:
- Check API_KEY is correct
- Check API_ENDPOINT matches your Azure resource
- Test your credentials at https://portal.azure.com

## Managing the Application

### View Logs

```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f backend
```

### Stop the Application

```bash
docker-compose -f docker-compose.prod.yml down
```

Your data is preserved in `mongodb_data` and `app_data` directories.

### Restart the Application

```bash
# Make sure you're in the hill-app directory
cd /path/to/hill-app

# Restart
docker-compose -f docker-compose.prod.yml up -d
```

### Update to Latest Version

```bash
# Navigate to your installation directory
cd /path/to/hill-app

# Pull and restart with latest version
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

## Configuration Options

### Change Ports

Edit `.env`:

```bash
FRONTEND_PORT=8080        # Change frontend port
MONGO_EXPRESS_PORT=8081   # Change database admin port
```

### Scale Workers

For better performance with many files:

```bash
docker-compose -f docker-compose.prod.yml up -d --scale worker=3
```

### Enable Database Admin UI

Start with MongoDB Express:

```bash
docker-compose -f docker-compose.prod.yml --profile tools up -d
```

Access at: http://localhost:8081
- Username: admin
- Password: admin (or what you set in .env)

## Data Backup

### Backup

```bash
# Backup everything
tar czf hill-backup-$(date +%Y%m%d).tar.gz mongodb_data app_data .env
```

### Restore

```bash
# Extract backup
tar xzf hill-backup-20240115.tar.gz

# Restart application
docker-compose -f docker-compose.prod.yml up -d
```

## Next Steps

1. **Upload your first file**: Create a project → Add a folder → Upload CSV/Excel
2. **Try AI auto-detection**: Open a file → Click "Auto-Detect" → Describe patterns
3. **Chat with your data**: Click the chat icon → Ask questions about your data
4. **Invite team members**: Share projects and folders for collaboration

## Getting Help

- **Documentation**: See [README.md](README.md) for full documentation
- **Troubleshooting**: Check logs with `docker-compose logs`
- **Issues**: Report at [GitHub Issues](https://github.com/houtj/time-series-labeling/issues)

## Uninstall

To completely remove the application:

```bash
# Stop and remove containers
docker-compose -f docker-compose.prod.yml down

# Remove data (careful - this deletes all your work!)
rm -rf mongodb_data app_data

# Remove downloaded images (optional)
docker rmi houtj1990/hill-sequence-backend
docker rmi houtj1990/hill-sequence-frontend
docker rmi houtj1990/hill-sequence-worker
```

---

**Need more control?** See [README.md](README.md) for advanced configuration and deployment options.

**Developer?** See [README.dev.md](README.dev.md) for development setup and contribution guidelines.

