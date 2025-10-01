# Hill Sequence Backend V2

A completely refactored version of the Hill Sequence backend with clean architecture, best practices, and modern Python patterns.

## 🎯 What's New in V2

### Architecture Improvements
- **Layered Architecture**: Clear separation of concerns (routes → services → repositories)
- **Dependency Injection**: Proper DI pattern throughout the application
- **Type Safety**: Full type hints and Pydantic validation
- **Error Handling**: Comprehensive exception hierarchy and handling
- **Configuration Management**: Environment-based configuration with Pydantic Settings
- **Logging**: Structured JSON logging for better observability

### Code Quality
- **Repository Pattern**: Clean data access layer
- **Service Layer**: Business logic separated from routes
- **No Code Duplication**: Consolidated similar operations
- **Async Best Practices**: Proper async/await usage
- **Security**: No hardcoded secrets, proper password management

## 📁 Project Structure

```
hill_backend_v2/
├── app/
│   ├── api/
│   │   ├── routes/          # API endpoints
│   │   │   ├── projects.py
│   │   │   ├── templates.py
│   │   │   ├── files.py
│   │   │   ├── folders.py
│   │   │   ├── labels.py
│   │   │   ├── users.py
│   │   │   ├── download.py
│   │   │   └── websockets.py
│   │   └── dependencies.py  # Dependency injection
│   ├── services/            # Business logic layer
│   │   ├── project.py
│   │   ├── template.py
│   │   ├── file.py
│   │   ├── folder.py
│   │   ├── label.py
│   │   ├── user.py
│   │   ├── download.py
│   │   ├── extraction.py
│   │   ├── chatbot.py
│   │   └── auto_detection/  # AI auto-detection
│   ├── repositories/        # Data access layer
│   │   ├── base.py
│   │   ├── project.py
│   │   ├── template.py
│   │   ├── file.py
│   │   ├── folder.py
│   │   ├── label.py
│   │   ├── user.py
│   │   └── conversation.py
│   ├── models/
│   │   └── schemas.py       # Pydantic models
│   └── core/
│       ├── config.py        # Configuration management
│       ├── database.py      # Database connection
│       ├── exceptions.py    # Custom exceptions
│       └── logging.py       # Logging setup
├── tests/                   # Test structure (ready for implementation)
├── main.py                  # Application entry point
├── pyproject.toml          # Project dependencies
└── README.md
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- MongoDB (running locally or remote)
- uv package manager (recommended) or pip

### Installation

1. **Clone and navigate to the directory**:
   ```bash
   cd /home/houtj/projects/hill_sequence/hill_backend_v2
   ```

2. **Install dependencies using uv**:
   ```bash
   uv sync
   ```

3. **Set up environment variables**:
   ```bash
   cp env.example .env
   ```
   
   Edit `.env` and configure:
   - `MONGODB_URL`: Your MongoDB connection string
   - `API_SECRET_KEY`: Generate a secure random key
   - `DOWNLOAD_API_PASSWORD`: Password for download endpoint
   - `AZURE_OPENAI_*`: Your Azure OpenAI credentials
   - Other settings as needed

4. **Run the application**:
   ```bash
   uv run python main.py
   ```
   
   Or with uvicorn directly:
   ```bash
   uv run uvicorn main:app --reload --host 0.0.0.0 --port 8001
   ```

The API will be available at `http://localhost:8001`

### API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

## 🔄 Migration from V1

### Key Differences

| Feature | V1 | V2 |
|---------|----|----|
| **Port** | 8000 | 8001 |
| **Architecture** | Monolithic | Layered |
| **Error Handling** | Mixed returns | Exception-based |
| **Configuration** | Scattered env vars | Centralized Pydantic Settings |
| **Type Safety** | Partial | Complete |
| **Logging** | Print statements | Structured JSON logging |
| **Security** | Hardcoded secrets | Environment-based |

### Running Both Versions

You can run both versions simultaneously for migration:

```bash
# Terminal 1 - Old backend (port 8000)
cd /home/houtj/projects/hill_sequence/hill_backend
python main.py

# Terminal 2 - New backend (port 8001)
cd /home/houtj/projects/hill_sequence/hill_backend_v2
uv run python main.py
```

### API Compatibility

All V1 endpoints are preserved in V2 with the same request/response formats. Simply change your client to point to port 8001.

**Example**:
- Old: `http://localhost:8000/projects`
- New: `http://localhost:8001/projects`

## 🏗️ Architecture Details

### Layered Architecture

```
Request → Route → Service → Repository → Database
   ↓         ↓        ↓          ↓           ↓
Response ← Format ← Logic ← Data ← MongoDB
```

1. **Routes** (`app/api/routes/`): HTTP endpoints, request validation, response formatting
2. **Services** (`app/services/`): Business logic, orchestration, data transformation
3. **Repositories** (`app/repositories/`): Database operations, queries, data access
4. **Models** (`app/models/`): Pydantic schemas for validation

### Dependency Injection

All dependencies are injected through FastAPI's dependency system:

```python
@router.post("/projects")
async def create_project(
    request: ProjectCreate,
    service: ProjectServiceDep  # Injected automatically
):
    return service.create_project(...)
```

### Configuration Management

All configuration is centralized in `app/core/config.py` using Pydantic Settings:

```python
from app.core.config import get_settings

settings = get_settings()
print(settings.mongodb_url)
```

## 📊 Key Features

### 1. Projects & Templates
- Create and manage projects
- Define data templates for different file types (.xlsx, .xls, .csv)
- Clone templates
- Extract column information

### 2. Files & Folders
- Upload files to folders
- Parse and store time-series data
- Download project files (password-protected)
- Manage file metadata and descriptions

### 3. Labels & Events
- Add events/labels to time-series data
- Define custom event classes with colors
- Add guidelines to charts
- Track labeling history

### 4. AI-Powered Features
- **Chat Assistant**: AI chatbot with tool access to add events/guidelines
- **Auto-Detection**: Automated event detection using multi-agent system
- WebSocket-based real-time communication

### 5. User Management
- User profiles and activity tracking
- Project and folder sharing
- Recent files tracking
- Collaboration features

## 🔧 Development

### Adding a New Feature

1. **Define Schema** (`app/models/schemas.py`):
   ```python
   class NewFeatureCreate(BaseModel):
       name: str
       description: str
   ```

2. **Add Repository Method** (`app/repositories/`):
   ```python
   def create_feature(self, data: dict) -> str:
       return self.create(data)
   ```

3. **Add Service Method** (`app/services/`):
   ```python
   def create_feature(self, name: str, description: str) -> dict:
       data = {"name": name, "description": description}
       feature_id = self.feature_repo.create(data)
       return {"id": feature_id, **data}
   ```

4. **Add Route** (`app/api/routes/`):
   ```python
   @router.post("/features")
   async def create_feature(
       request: NewFeatureCreate,
       service: FeatureServiceDep
   ):
       return service.create_feature(request.name, request.description)
   ```

### Running Tests

```bash
# Install dev dependencies
uv sync --all-extras

# Run tests (when implemented)
uv run pytest

# With coverage
uv run pytest --cov=app
```

### Code Formatting

```bash
# Format code
uv run black app/

# Lint code
uv run ruff check app/
```

## 🔐 Security

- **No Hardcoded Secrets**: All secrets in environment variables
- **Password Protection**: Download endpoint requires password
- **CORS Configuration**: Configurable allowed origins
- **Input Validation**: Pydantic validation on all inputs
- **Exception Handling**: No sensitive data leakage in errors

## 📝 Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `MONGODB_URL` | MongoDB connection string | ✅ | - |
| `DATABASE_NAME` | Database name | ❌ | `hill_ts` |
| `DATA_FOLDER_PATH` | File storage path | ❌ | `./data_folder` |
| `API_SECRET_KEY` | Secret key for API | ✅ | - |
| `DOWNLOAD_API_PASSWORD` | Password for downloads | ✅ | - |
| `CORS_ORIGINS` | Allowed CORS origins | ❌ | `*` |
| `AZURE_OPENAI_*` | Azure OpenAI credentials | ✅ | - |
| `DEBUG` | Enable debug mode | ❌ | `false` |
| `PORT` | Server port | ❌ | `8001` |

## 🤝 Contributing

This is a refactored version with improved:
- Code organization
- Type safety
- Error handling
- Security
- Testability
- Documentation

## 📄 License

Same as the original Hill Sequence project.

## 🆚 Comparison with V1

### Lines of Code Reduction

- **V1 main.py**: 661 lines
- **V2 total**: ~50 small, focused files averaging ~100 lines each
- **Improvement**: Better maintainability, reusability, testability

### Benefits

✅ **Maintainability**: Each file has a single responsibility  
✅ **Testability**: Services and repositories easy to unit test  
✅ **Scalability**: Easy to add new features without touching existing code  
✅ **Type Safety**: Catch errors at development time, not runtime  
✅ **Security**: Centralized configuration, no hardcoded secrets  
✅ **Documentation**: Self-documenting code with type hints  

## 📞 Support

For issues or questions about the refactored backend, refer to the original project documentation or examine the well-structured code in `app/`.

---

**Built with ❤️ using FastAPI, MongoDB, and Clean Architecture principles**

