# Hill Sequence - Time Series Labeling Tool

A comprehensive time-series labeling tool for visualizing, annotating, and analyzing time-series data with AI-powered assistance.

## Features

- **Interactive Visualization**: Plot and visualize time-series data with multiple channels
- **Manual Labeling**: Create events and guidelines on your time-series data
- **AI-Powered Auto-Detection**: Automatically detect patterns and events using Azure OpenAI
- **AI Chat Assistant**: Get insights and analysis of your data through natural language
- **File Support**: Import CSV and Excel files with flexible template configuration
- **Project Management**: Organize your work with projects, folders, and reusable templates
- **Collaborative**: Share projects and folders with team members

## Quick Start

### Prerequisites

- Docker and Docker Compose installed on your system
- At least 4GB of available RAM
- 10GB of available disk space
- Azure OpenAI API credentials (for AI features)

### Installation

1. **Create a deployment directory**:
   ```bash
   mkdir hill-app && cd hill-app
   ```

2. **Download required files**:
   ```bash
   curl -O https://raw.githubusercontent.com/houtj/time-series-labeling/main/docker-compose.prod.yml
   curl -O https://raw.githubusercontent.com/houtj/time-series-labeling/main/env.example
   curl -O https://raw.githubusercontent.com/houtj/time-series-labeling/main/init-mongo.js
   
   # Create data directories
   mkdir -p mongodb_data app_data
   ```

3. **Configure your environment**:
   ```bash
   cp env.example .env
   ```
   
   Edit `.env` and add your Azure OpenAI credentials:
   ```bash
   AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
   API_VERSION=2024-02-01
   API_KEY=your-azure-openai-key-here
   API_ENDPOINT=https://your-resource.openai.azure.com/
   ```
   
   **Don't have Azure OpenAI?** Visit [Azure OpenAI Service](https://azure.microsoft.com/en-us/products/ai-services/openai-service) to get started. The application will run without it, but AI features will be unavailable.

4. **Start the application**:
   ```bash
   # IMPORTANT: Run from the hill-app directory
   docker-compose -f docker-compose.prod.yml up -d
   ```
   
   **Note**: Always run docker-compose from the same directory containing the docker-compose.prod.yml file. Data will be stored in `./mongodb_data` and `./app_data` relative to this location.

5. **Access the application**:
   - Open your browser to: http://localhost:4200
   - The application will load and be ready to use

### One-Line Installation

For the fastest setup, use this single command:

```bash
mkdir hill-app && cd hill-app && \
curl -O https://raw.githubusercontent.com/houtj/time-series-labeling/main/docker-compose.prod.yml && \
curl -O https://raw.githubusercontent.com/houtj/time-series-labeling/main/env.example && \
curl -O https://raw.githubusercontent.com/houtj/time-series-labeling/main/init-mongo.js && \
mkdir -p mongodb_data app_data && \
cp env.example .env && \
echo "Edit .env with your OpenAI credentials, then run: docker-compose -f docker-compose.prod.yml up -d"
```

## Usage

### Creating a Project

1. Navigate to the Projects page
2. Click "New Project"
3. Define your event classes (e.g., "Running", "Idle", "Error")
4. Create templates for your file formats

### Importing Data

1. Create a folder within your project
2. Upload CSV or Excel files
3. Files are automatically parsed based on your template
4. Start labeling!

### Labeling Events

1. Open a file in the labeling interface
2. Click and drag to create event regions
3. Assign event classes to regions
4. Add guidelines for reference lines
5. Use AI auto-detection for automatic pattern recognition

### AI Features

**Auto-Detection**: Automatically detect events in your time-series data
- Click "Auto-Detect" in the labeling interface
- Describe what patterns to look for
- Review and accept detected events

**AI Chat**: Ask questions about your data
- Open the chat panel
- Ask natural language questions
- Get insights and analysis

## Configuration

### Environment Variables

Edit your `.env` file to configure:

| Variable | Description | Default |
|----------|-------------|---------|
| `MONGO_ROOT_PASSWORD` | MongoDB admin password | example |
| `FRONTEND_PORT` | Application port | 4200 |
| `WORKER_REPLICAS` | Number of worker processes | 1 |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | OpenAI model deployment | gpt-4 |
| `API_KEY` | Your Azure OpenAI API key | (required) |
| `API_ENDPOINT` | Your Azure OpenAI endpoint | (required) |

**Security Note**: Change the default `MONGO_ROOT_PASSWORD` for production use.

### Data Persistence

Your data is stored in directories relative to where you run docker-compose:
- `./mongodb_data` - Database files
- `./app_data` - Uploaded files and parsed data

**Important**: 
- Always run docker-compose from the same directory (where docker-compose.prod.yml is located)
- These directories are created automatically on first run
- Data persists across container restarts and upgrades
- For production, consider using absolute paths in your `.env` file:
  ```bash
  MONGODB_DATA_PATH=/opt/hill-app/mongodb_data
  APP_DATA_PATH=/opt/hill-app/app_data
  ```

## Management

### Viewing Logs

```bash
# Navigate to your installation directory first
cd /path/to/hill-app

# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f backend
```

### Stopping the Application

```bash
# Navigate to your installation directory
cd /path/to/hill-app

# Stop all services
docker-compose -f docker-compose.prod.yml down
```

### Updating to New Version

```bash
# Navigate to your installation directory
cd /path/to/hill-app

# Set the version you want (optional, defaults to latest)
export VERSION=v1.2.0

# Pull and restart
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

### Scaling Workers

For better performance with many files:

```bash
# Navigate to your installation directory
cd /path/to/hill-app

# Scale to 3 workers
docker-compose -f docker-compose.prod.yml up -d --scale worker=3
```

## Troubleshooting

### Port Already in Use

If port 4200 is already in use, change it in your `.env` file:
```bash
FRONTEND_PORT=4201
```

Then restart:
```bash
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d
```

### Cannot Connect to Application

1. Check if all services are running:
   ```bash
   docker-compose -f docker-compose.prod.yml ps
   ```

2. Check service health:
   ```bash
   docker-compose -f docker-compose.prod.yml logs backend
   docker-compose -f docker-compose.prod.yml logs frontend
   ```

3. Verify network connectivity:
   ```bash
   curl http://localhost:4200
   ```

### AI Features Not Working

1. Verify your Azure OpenAI credentials in `.env`
2. Check backend logs:
   ```bash
   docker-compose -f docker-compose.prod.yml logs backend
   ```
3. Ensure your OpenAI endpoint is accessible from your network

### Files Not Processing

1. Check worker logs:
   ```bash
   docker-compose -f docker-compose.prod.yml logs worker
   ```
2. Verify Redis is running:
   ```bash
   docker-compose -f docker-compose.prod.yml ps redis
   ```

## Data Backup

### Backup Your Data

```bash
# Backup database
docker-compose -f docker-compose.prod.yml exec mongodb mongodump --out /backup

# Backup files
tar czf backup-$(date +%Y%m%d).tar.gz mongodb_data app_data
```

### Restore from Backup

```bash
# Restore database
docker-compose -f docker-compose.prod.yml exec mongodb mongorestore /backup

# Restore files
tar xzf backup-20240115.tar.gz
```

## System Requirements

### Minimum
- 2 CPU cores
- 4GB RAM
- 10GB disk space
- Docker 20.10+
- Docker Compose 2.0+

### Recommended
- 4+ CPU cores
- 8GB+ RAM
- 50GB+ disk space (depending on data volume)

## Support

For questions, issues, or feature requests:
- Check the [Troubleshooting](#troubleshooting) section
- Review service logs for error messages
- Contact your system administrator

## Contributing

Interested in contributing? See [README.dev.md](README.dev.md) for development setup and guidelines.

## License

[Add your license information here]
