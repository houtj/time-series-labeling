"""
Hill Sequence Backend v1.5
Refactored backend with clean route organization
"""
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request

from config import settings
from database import init_database
from redis_client import init_redis

# Import route modules
from routes import (
    projects,
    templates,
    files,
    folders,
    labels,
    users,
    chat_conversations,
    detection_conversations
)

# Import WebSocket handlers
from ws_handlers.chat import handle_websocket as handle_chat_ws
from ws_handlers.auto_detect import handle_websocket as handle_auto_detect_ws

# Initialize app
app = FastAPI(
    title="Hill Sequence Backend",
    description="Time series data labeling platform",
    version="1.5.0"
)


# ============================================================================
# Middleware Configuration
# ============================================================================

class LargeFileMiddleware(BaseHTTPMiddleware):
    """Middleware to handle large file uploads"""
    async def dispatch(self, request: Request, call_next):
        request.scope["max_content_size"] = settings.MAX_UPLOAD_SIZE_BYTES
        response = await call_next(request)
        return response


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add large file middleware
app.add_middleware(LargeFileMiddleware)


# ============================================================================
# Database & Redis Initialization
# ============================================================================

# Initialize database on startup
db = init_database()

# Initialize Redis on startup
init_redis()


# ============================================================================
# Health Check
# ============================================================================

@app.get("/", tags=["health"])
async def root():
    """Health check endpoint"""
    return {
        'hello': 'world', 
        'version': '1.5.0', 
        'status': 'healthy'
    }


# ============================================================================
# REST API Routes
# ============================================================================

app.include_router(projects.router)
app.include_router(templates.router)
app.include_router(files.router)
app.include_router(folders.router)
app.include_router(labels.router)
app.include_router(users.router)
app.include_router(chat_conversations.router)
app.include_router(detection_conversations.router)


# ============================================================================
# WebSocket Endpoints
# ============================================================================

@app.websocket("/ws/chat/{file_id}")
async def websocket_chat(websocket: WebSocket, file_id: str):
    """Chat WebSocket endpoint"""
    await handle_chat_ws(websocket, file_id)


@app.websocket("/ws/auto-detection/{file_id}")
async def websocket_auto_detection(websocket: WebSocket, file_id: str):
    """Auto-detection WebSocket endpoint"""
    await handle_auto_detect_ws(websocket, file_id)


# ============================================================================
# Application Entry Point
# ============================================================================

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(
        'main:app', 
        host=settings.HOST, 
        port=settings.PORT, 
        reload=settings.DEBUG,
        # ws='none'  # Disable auto websocket detection, use FastAPI's built-in
    )
