"""
Pydantic Models
Contains both database entity models and API request models
Keep database entities in sync with frontend/src/app/model.ts
"""
from pydantic import BaseModel
from typing import Optional, List, Literal


# ==========================================
# DATABASE ENTITY MODELS
# Mirror from frontend model.ts
# Keep in sync when schema changes
# ==========================================

class ProjectClass(BaseModel):
    """Event class definition"""
    name: str
    color: str
    description: str


class ProjectTemplate(BaseModel):
    """Template reference in project"""
    id: str
    name: str
    fileType: str


class ProjectModel(BaseModel):
    """Project entity - mirrors frontend ProjectModel"""
    projectName: str
    templates: List[ProjectTemplate] = []
    classes: List[ProjectClass] = []
    general_pattern_description: str = ""


class TemplateChannel(BaseModel):
    """Channel configuration in template"""
    channelName: str
    color: str
    regex: str
    mandatory: bool
    unit: str


class TemplateX(BaseModel):
    """X-axis configuration"""
    name: str
    regex: str
    isTime: bool
    unit: str


class TemplateModel(BaseModel):
    """Template entity - mirrors frontend TemplateModel"""
    fileType: str
    templateName: str
    sheetName: str
    headRow: int
    skipRow: int
    x: TemplateX
    channels: List[TemplateChannel] = []


class FileModel(BaseModel):
    """File entity - mirrors frontend FileModel"""
    name: str
    parsing: str  # "uploading" | "parsing start" | "parsed"
    nbEvent: str  # "unlabeled" | "3 by Alice; 2 by Bob"
    description: str
    rawPath: str
    jsonPath: str
    label: str  # ObjectId as string
    lastModifier: str
    chatConversationId: str = None  # ObjectId of chat conversation
    autoDetectionConversationId: str = None  # ObjectId of auto-detection conversation


class FolderModel(BaseModel):
    """Folder entity - mirrors frontend FolderModel"""
    name: str
    project: dict  # {id: str, name: str}
    template: dict  # {id: str, name: str}
    nbLabeledFiles: int
    nbTotalFiles: int
    fileList: List[str] = []


class LabelEvent(BaseModel):
    """Event in a label"""
    className: str
    color: str
    description: str
    labeler: str
    start: str | int | float
    end: str | int | float
    hide: bool


class LabelGuideline(BaseModel):
    """Guideline in a label"""
    yaxis: str
    y: str | int | float
    channelName: str
    color: str
    hide: bool


class LabelModel(BaseModel):
    """Label entity - mirrors frontend LabelModel"""
    events: List[LabelEvent] = []
    guidelines: List[LabelGuideline] = []


class UserRecentFile(BaseModel):
    """Recent file reference"""
    folder: str
    file: str
    displayText: str


class UserMessage(BaseModel):
    """User notification message"""
    folder: str = ""
    file: str = ""
    project: str = ""
    displayText: str


class UserModel(BaseModel):
    """User entity - mirrors frontend UserModel"""
    name: str
    mail: str
    folderList: List[str] = []
    projectList: List[str] = []
    recent: List[UserRecentFile] = []
    message: List[UserMessage] = []
    badge: str
    rank: int


class ChatMessage(BaseModel):
    """Single chat message"""
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: str


class ChatConversation(BaseModel):
    """Chat conversation for a file"""
    fileId: str
    messages: List[ChatMessage] = []
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None


class AutoDetectionMessage(BaseModel):
    """Auto-detection progress message"""
    type: Literal["status", "progress", "result", "error"]
    status: str  # started, planning, identifying, validating, completed, failed
    message: str
    timestamp: str
    eventsDetected: Optional[int] = None
    summary: Optional[str] = None
    error: Optional[str] = None


class AutoDetectionConversation(BaseModel):
    """Auto-detection conversation for a file"""
    fileId: str
    messages: List[AutoDetectionMessage] = []
    status: Literal["idle", "started", "running", "completed", "failed"] = "idle"
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None


# ==========================================
# API REQUEST MODELS
# Used for endpoint inputs
# ==========================================

class NewProjectRequest(BaseModel):
    """Create new project"""
    projectName: str
    userId: str


class NewTemplateRequest(BaseModel):
    """Create new template"""
    templateName: str
    projectId: str
    fileType: str


class UpdateTemplateRequest(BaseModel):
    """Update template"""
    request: dict
    projectId: str


class CloneTemplateRequest(BaseModel):
    """Clone template"""
    newTemplateName: str
    projectId: str
    templateId: str


class NewClassRequest(BaseModel):
    """Add class to project"""
    newClassName: str
    projectId: str
    newClassColor: str
    description: str


class UpdateClassRequest(BaseModel):
    """Update existing class"""
    updatingClassName: str
    newClassName: str
    newClassColor: str
    description: str
    projectId: str


class NewFolderRequest(BaseModel):
    """Create new folder"""
    newFolderName: str
    project: dict
    template: dict
    userId: str


class UpdateUserSharedFolderRequest(BaseModel):
    """Share folder with user"""
    folder: dict
    user: dict
    userName: str
    message: str


class UpdateUserShareProjectRequest(BaseModel):
    """Share project with user"""
    project: dict
    user: dict
    userName: str
    message: str


class UpdateLabelRequest(BaseModel):
    """Update label"""
    label: dict
    user: str


class UpdateUserRecentFilesRequest(BaseModel):
    """Update user's recent files"""
    folderId: str
    fileId: str
    fileName: str
    folderName: str
    userInfo: dict


class UpdateDescriptionRequest(BaseModel):
    """Update file description"""
    file_id: str
    description: str


class DownloadJsonFilesRequest(BaseModel):
    """Download project files"""
    projectId: str
    passwd: str


class ReparsingFilesRequest(BaseModel):
    """Trigger file reparsing"""
    folderId: str


class UpdateProjectDescriptionsRequest(BaseModel):
    """Update project descriptions"""
    projectId: str
    generalDescription: str
    classDescriptions: List[dict]


class SendChatMessageRequest(BaseModel):
    """Send a chat message"""
    message: str


class WindowFeaturesRequest(BaseModel):
    """Request window feature computation"""
    file_id: str
    start: int
    end: int

