# Architecture Documentation

## Overview

Hill Sequence Backend V2 follows **Clean Architecture** principles with clear separation of concerns and dependency inversion.

## Architecture Layers

```
┌─────────────────────────────────────────────────────────┐
│                    API Layer (Routes)                    │
│  - HTTP endpoints                                        │
│  - Request validation (Pydantic)                         │
│  - Response formatting                                   │
│  - WebSocket handling                                    │
└────────────────────┬────────────────────────────────────┘
                     │ depends on
┌────────────────────▼────────────────────────────────────┐
│                   Service Layer                          │
│  - Business logic                                        │
│  - Orchestration                                         │
│  - Data transformation                                   │
│  - Cross-cutting concerns                                │
└────────────────────┬────────────────────────────────────┘
                     │ depends on
┌────────────────────▼────────────────────────────────────┐
│                  Repository Layer                        │
│  - Database operations                                   │
│  - Query building                                        │
│  - Data access abstraction                               │
└────────────────────┬────────────────────────────────────┘
                     │ depends on
┌────────────────────▼────────────────────────────────────┐
│                   Database (MongoDB)                     │
│  - Data persistence                                      │
│  - Collections: projects, files, folders, etc.           │
└─────────────────────────────────────────────────────────┘
```

## Dependency Flow

```
main.py
  ├── app/core/
  │   ├── config.py         → Settings & configuration
  │   ├── database.py       → DB connection management
  │   ├── exceptions.py     → Custom exception classes
  │   └── logging.py        → Logging configuration
  │
  ├── app/api/
  │   ├── dependencies.py   → DI container
  │   └── routes/
  │       ├── projects.py   → Project endpoints
  │       ├── templates.py  → Template endpoints
  │       ├── files.py      → File endpoints
  │       ├── folders.py    → Folder endpoints
  │       ├── labels.py     → Label endpoints
  │       ├── users.py      → User endpoints
  │       ├── download.py   → Download endpoints
  │       └── websockets.py → WebSocket endpoints
  │
  ├── app/services/
  │   ├── project.py        → Project business logic
  │   ├── template.py       → Template business logic
  │   ├── file.py           → File business logic
  │   ├── folder.py         → Folder business logic
  │   ├── label.py          → Label business logic
  │   ├── user.py           → User business logic
  │   ├── download.py       → Download business logic
  │   ├── extraction.py     → File extraction logic
  │   ├── chatbot.py        → AI chat functionality
  │   └── auto_detection/   → AI auto-detection
  │
  ├── app/repositories/
  │   ├── base.py           → Base repository (CRUD)
  │   ├── project.py        → Project data access
  │   ├── template.py       → Template data access
  │   ├── file.py           → File data access
  │   ├── folder.py         → Folder data access
  │   ├── label.py          → Label data access
  │   ├── user.py           → User data access
  │   └── conversation.py   → Conversation data access
  │
  └── app/models/
      └── schemas.py        → Pydantic models
```

## Design Patterns

### 1. Repository Pattern

Abstracts data access logic from business logic.

**Benefits**:
- Database operations centralized
- Easy to test (mock repositories)
- Can swap database implementations

**Example**:
```python
class ProjectRepository(BaseRepository):
    def add_template(self, project_id: str, template: dict) -> bool:
        return self.update_one(
            {"_id": ObjectId(project_id)},
            {"$push": {"templates": template}}
        )
```

### 2. Service Layer Pattern

Encapsulates business logic separate from data access and presentation.

**Benefits**:
- Business rules in one place
- Reusable across different interfaces
- Easier to test

**Example**:
```python
class ProjectService:
    def create_project(self, name: str, user_id: str) -> dict:
        # Validate user exists
        user = self.user_repo.find_by_id(user_id)
        if not user:
            raise NotFoundException("User", user_id)
        
        # Create project
        project = {...}
        project_id = self.project_repo.create(project)
        
        # Add to user's list
        self.user_repo.add_project(user_id, project_id)
        
        return project
```

### 3. Dependency Injection

All dependencies are injected via FastAPI's DI system.

**Benefits**:
- Loose coupling
- Easy testing
- Clear dependencies

**Example**:
```python
@router.post("/projects")
async def create_project(
    request: ProjectCreate,
    service: Annotated[ProjectService, Depends(get_project_service)]
):
    return service.create_project(request.projectName, request.userId)
```

### 4. Exception-Based Error Handling

Custom exceptions for different error types.

**Benefits**:
- Consistent error responses
- Clear error semantics
- Easy to handle in middleware

**Example**:
```python
class NotFoundException(HTTPException):
    def __init__(self, resource: str, identifier: str):
        super().__init__(
            status_code=404,
            detail=f"{resource} with identifier '{identifier}' not found"
        )
```

## Data Flow Example

### Creating a Project

```
1. Client sends POST /projects
   ↓
2. Route validates request (Pydantic)
   ↓
3. Route calls ProjectService.create_project()
   ↓
4. Service validates user exists via UserRepository
   ↓
5. Service creates project via ProjectRepository
   ↓
6. Service adds project to user via UserRepository
   ↓
7. Service returns project data
   ↓
8. Route formats response (dumps to JSON)
   ↓
9. Client receives response
```

### Adding an Event via AI Chat

```
1. Client sends message via WebSocket
   ↓
2. WebSocket handler receives message
   ↓
3. Handler calls chatbot.handle_chat_message()
   ↓
4. Chatbot adds message to conversation history
   ↓
5. Chatbot calls LangChain agent with message
   ↓
6. Agent decides to use AddEventTool
   ↓
7. Tool accesses database via get_sync_database()
   ↓
8. Tool validates and creates event
   ↓
9. Tool queues WebSocket notification
   ↓
10. Handler sends notifications to client
    ↓
11. Client receives event and updates UI
```

## Configuration Management

Using Pydantic Settings for type-safe configuration:

```python
class Settings(BaseSettings):
    mongodb_url: str = Field(..., alias="MONGODB_URL")
    api_secret_key: str = Field(..., alias="API_SECRET_KEY")
    
    class Config:
        env_file = ".env"

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

**Benefits**:
- Type validation
- Environment variable parsing
- Default values
- Singleton pattern (cached)

## Database Design

### Collections

```
projects
  - _id: ObjectId
  - projectName: string
  - templates: array[{id, name, fileType}]
  - classes: array[{name, color, description}]
  - general_pattern_description: string

templates
  - _id: ObjectId
  - templateName: string
  - fileType: string (.xlsx, .xls, .csv)
  - channels: array
  - x: object
  - headRow: int
  - skipRow: int
  - sheetName: string/int

folders
  - _id: ObjectId
  - name: string
  - project: {id, name}
  - template: {id, name}
  - fileList: array[string]
  - nbLabeledFiles: int
  - nbTotalFiles: int

files
  - _id: ObjectId
  - name: string
  - parsing: string (uploading, parsing start, parsed)
  - nbEvent: string (unlabeled, or "X by User")
  - description: string
  - rawPath: string
  - jsonPath: string
  - lastModifier: string
  - lastUpdate: datetime
  - label: string (ObjectId ref)

labels
  - _id: ObjectId
  - events: array[{className, color, description, labeler, start, end, hide}]
  - guidelines: array[{yaxis, y, channelName, color, hide}]

users
  - _id: ObjectId
  - name: string
  - mail: string
  - activeSince: datetime
  - projectList: array[string]
  - folderList: array[string]
  - recent: array[{folder, file, displayText}]
  - message: array[object]
  - badge: string
  - rank: int

conversations
  - _id: ObjectId
  - fileId: string
  - history: array[{role, content, timestamp}]
```

## Testing Strategy

### Unit Tests
- Test services with mocked repositories
- Test repositories with MongoDB mock
- Test utilities and helpers

### Integration Tests
- Test API endpoints with TestClient
- Test database operations
- Test WebSocket connections

### End-to-End Tests
- Test complete workflows
- Test with real database (test instance)

## Security Considerations

1. **No Hardcoded Secrets**: All in environment variables
2. **Input Validation**: Pydantic validates all inputs
3. **Exception Handling**: No sensitive data in error messages
4. **CORS**: Configurable allowed origins
5. **Password Protection**: Download endpoint secured
6. **Type Safety**: Prevents many runtime errors

## Performance Optimizations

1. **Connection Pooling**: MongoDB client pools connections
2. **Async/Await**: Non-blocking I/O operations
3. **Lazy Loading**: Settings cached with lru_cache
4. **Efficient Queries**: Repository layer optimizes queries
5. **Streaming**: Large file uploads handled efficiently

## Extensibility

### Adding a New Entity

1. Create repository in `app/repositories/new_entity.py`
2. Create service in `app/services/new_entity.py`
3. Add dependency in `app/api/dependencies.py`
4. Create routes in `app/api/routes/new_entity.py`
5. Define schemas in `app/models/schemas.py`

### Adding a New Feature to Existing Entity

1. Add method to repository
2. Add business logic to service
3. Add route endpoint
4. Update schemas if needed

## Monitoring & Observability

### Logging

Structured JSON logging with:
- Timestamp
- Log level
- Logger name
- Message
- Context

### Metrics (Future)

Can add:
- Request duration
- Error rates
- Database query times
- Active connections

### Health Checks

- Database connectivity
- API responsiveness
- Disk space

## Best Practices Followed

1. ✅ **Single Responsibility**: Each class/module has one job
2. ✅ **Dependency Inversion**: Depend on abstractions
3. ✅ **Open/Closed**: Open for extension, closed for modification
4. ✅ **DRY**: Don't Repeat Yourself
5. ✅ **KISS**: Keep It Simple, Stupid
6. ✅ **Type Hints**: Full type coverage
7. ✅ **Documentation**: Code is self-documenting
8. ✅ **Error Handling**: Comprehensive exception handling
9. ✅ **Separation of Concerns**: Clear layer boundaries
10. ✅ **Testability**: Easy to write tests

## Future Enhancements

1. **Authentication/Authorization**: JWT-based auth
2. **Rate Limiting**: Prevent abuse
3. **Caching**: Redis for frequent queries
4. **Async Repositories**: Full async database access
5. **GraphQL**: Alternative to REST
6. **Event Sourcing**: Track all changes
7. **Metrics**: Prometheus/Grafana
8. **API Versioning**: Support multiple versions

---

This architecture provides a **solid foundation** for long-term maintainability and scalability.

