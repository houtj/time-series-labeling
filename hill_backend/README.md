# Hill Sequence Backend v1.5

Refactored backend with clean architecture and improved maintainability.

> **For development setup and contribution guidelines**, see [README.dev.md](../README.dev.md) in the project root.

## 🎯 What's New in v1.5

### Architecture Improvements
- ✅ **Route organization**: Split into 8 route files by resource
- ✅ **Agent system**: Unified `agents/` folder for chat and auto-detection
- ✅ **WebSocket handlers**: Separate handlers in `websockets/` folder
- ✅ **Simplified database**: Only connection management, no mixed concerns
- ✅ **Configuration management**: Centralized settings in `config.py`
- ✅ **Two conversation collections**: Separate chat and auto-detection conversations

### File Structure
```
hill_backend_v1.5/
├── main.py                          # Clean entry point (~120 lines)
├── config.py                        # Settings & env vars
├── database.py                      # DB connection only
├── models.py                        # All Pydantic models
│
├── routes/                          # REST API endpoints (8 files)
│   ├── projects.py
│   ├── templates.py
│   ├── files.py
│   ├── folders.py
│   ├── labels.py
│   ├── users.py
│   ├── chat_conversations.py        # NEW: Chat conversation endpoints
│   └── detection_conversations.py   # NEW: Auto-detection conversation endpoints
│
├── websockets/                      # WebSocket endpoints (2 files)
│   ├── chat.py
│   └── auto_detect.py
│
└── agents/                          # AI Agent System
    ├── chat/                        # Chat assistant
    │   └── agent.py
    │
    └── auto_detect/                 # Auto-detection multi-agent
        ├── coordinator.py
        ├── planner.py
        ├── identifier.py
        ├── validator.py
        ├── tools.py
        ├── utils.py
        ├── models.py
        └── prompts.py
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd hill_backend_v1.5
uv sync
```

### 2. Configure Environment
```bash
# Copy .env from v1 or create new one
cp ../.env .env

# Or create from scratch
cat > .env << EOF
MONGODB_URL=mongodb://root:example@localhost:27017/
DATA_FOLDER_PATH=./data_folder
DOWNLOAD_PASSWORD=your-password-here
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4.1
API_VERSION=2024-02-01
API_KEY=your-api-key
API_ENDPOINT=your-endpoint
DEBUG=True
EOF
```

### 3. Run the Server
```bash
uv run python main.py
```

The server will start on `http://localhost:8000`

## 📊 Database Collections

### Existing Collections (from v1)
- `users` - User accounts
- `projects` - Projects
- `templates` - Templates
- `folders` - Folders
- `files` - Files
- `labels` - Labels/events

### New Collections (v1.5)
- `chat_conversations` - Chat conversation history per file
- `auto_detection_conversations` - Auto-detection progress per file

## 🔌 API Endpoints

### Projects
- `POST /projects` - Create project
- `GET /projects` - Get projects
- `PUT /projects/descriptions` - Update descriptions

### Templates
- `POST /templates` - Create template
- `GET /templates/{id}` - Get template
- `PUT /templates` - Update template
- `PUT /templates/clone` - Clone template
- `POST /templates/extract-columns` - Extract columns from file

### Files
- `POST /files` - Upload files
- `GET /files` - Get multiple files
- `GET /files/{id}` - Get file with data
- `DELETE /files` - Delete file
- `PUT /files/descriptions` - Update description
- `PUT /files/reparse` - Trigger reparsing
- `GET /files/data/{folder_id}` - Get all file data
- `GET /files/events/{folder_id}` - Get all events
- `POST /files/jsonfiles` - Bulk download (password protected)

### Folders
- `POST /folders` - Create folder
- `GET /folders` - Get folders
- `GET /folders/{id}` - Get folder
- `DELETE /folders` - Delete folder

### Labels
- `GET /labels/{id}` - Get label
- `PUT /labels` - Update label
- `POST /labels/event` - Add single event
- `POST /labels/events` - Add bulk events
- `POST /labels/classes` - Add class
- `PUT /labels/classes` - Update class

### Users
- `GET /users/info` - Get user info
- `GET /users` - Get all users
- `PUT /users/shared-folders` - Share folder
- `PUT /users/shared-files` - Share files
- `PUT /users/shared-projects` - Share project
- `PUT /users/recent-files` - Update recent files

### Chat Conversations (NEW)
- `GET /conversations/chat/{file_id}` - Get chat conversation
- `DELETE /conversations/chat/{file_id}` - Clear chat conversation
- `GET /conversations/chat/{file_id}/messages/recent` - Get recent messages

### Auto-Detection Conversations (NEW)
- `GET /conversations/detection/{file_id}` - Get detection conversation
- `DELETE /conversations/detection/{file_id}` - Clear detection conversation
- `GET /conversations/detection/{file_id}/latest` - Get latest run
- `GET /conversations/detection/{file_id}/history` - Get all runs

### WebSockets
- `WS /ws/chat/{file_id}` - Chat assistant
- `WS /ws/auto-detection/{file_id}` - Auto-detection agent

## 🔧 Development

### Project Structure Principles
1. **Routes** = HTTP endpoints organized by resource
2. **WebSockets** = Bidirectional communication handlers
3. **Agents** = AI business logic (protocol-agnostic)
4. **Models** = Pydantic validation (entities + requests)
5. **Database** = Connection management only

### Adding New Features

#### Add New Route
```python
# routes/new_feature.py
from fastapi import APIRouter
from database import get_db

router = APIRouter(prefix="/new-feature", tags=["new-feature"])

@router.get("")
async def get_new_feature():
    db = get_db()
    # Your logic here
    return {"status": "ok"}
```

Then add to `main.py`:
```python
from routes import new_feature
app.include_router(new_feature.router)
```

#### Add New Model
```python
# models.py

# Database entity (mirror frontend)
class NewEntityModel(BaseModel):
    field1: str
    field2: int

# API request
class NewEntityRequest(BaseModel):
    data: str
```

## 🎯 Key Improvements Over v1

| Aspect | v1 | v1.5 |
|--------|-----|------|
| **Files** | 8 files | 27 files |
| **main.py** | 661 lines | ~120 lines |
| **Organization** | Everything in main.py | Clear separation |
| **Conversations** | Mixed in database.py | 2 dedicated routes |
| **Agents** | 2 separate folders | Unified agents/ |
| **WebSockets** | 1 mixed file | 2 separate handlers |
| **Collections** | N/A | 2 new conversation collections |

## 📝 Migration from v1

The v1.5 backend is **fully compatible** with v1. You can run both simultaneously on different ports.

### Database Changes
v1.5 adds two new collections:
- `chat_conversations` - Indexed on `fileId`
- `auto_detection_conversations` - Indexed on `fileId`

These are created automatically on first run.

### No Breaking Changes
All existing API endpoints remain unchanged. The conversation endpoints are additions, not replacements.

## 🐛 Troubleshooting

### Import Errors
```bash
# Make sure you're in the virtual environment
source .venv/bin/activate  # or use 'uv run'
```

### Database Connection Issues
```bash
# Check MongoDB is running
docker-compose up -d mongodb  # if using docker

# Verify connection string in .env
MONGODB_URL=mongodb://root:example@localhost:27017/
```

### Port Already in Use
```bash
# Change port in config.py or .env
PORT=8001

# Or in main.py
uvicorn.run('main:app', host="0.0.0.0", port=8001, reload=True)
```

## 📦 Dependencies

Managed with `uv`:
- FastAPI & Uvicorn - Web framework
- PyMongo - MongoDB driver
- Pydantic - Data validation
- LangChain & OpenAI - AI agents
- Pandas, openpyxl, xlrd - File processing
- Python-multipart, aiofiles - File uploads

## 🚀 Deployment

### Docker (Recommended)
```bash
# Build image
docker build -t hill-backend-v1.5 .

# Run container
docker run -p 8000:8000 --env-file .env hill-backend-v1.5
```

### Direct
```bash
# Install dependencies
uv sync

# Run with production settings
DEBUG=False uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

## 📄 License

Same as the main Hill Sequence project.

## 🤝 Contributing

1. Follow the existing file structure
2. Add models to `models.py`
3. Create routes in `routes/`
4. Keep agents protocol-agnostic
5. Update this README

---

**v1.5** - A cleaner, more maintainable backend 🚀

