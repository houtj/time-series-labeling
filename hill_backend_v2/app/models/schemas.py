"""Pydantic schemas for request/response validation"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Common/Shared Schemas
# ============================================================================


class SuccessResponse(BaseModel):
    """Standard success response"""

    success: bool = True
    message: str = "Operation completed successfully"
    data: dict[str, Any] | None = None


class ErrorResponse(BaseModel):
    """Standard error response"""

    success: bool = False
    error: str
    detail: str | None = None


class IDReference(BaseModel):
    """Reference to another entity by ID"""

    id: str
    name: str


# ============================================================================
# Project Schemas
# ============================================================================


class ProjectCreate(BaseModel):
    """Schema for creating a new project"""

    projectName: str = Field(..., min_length=1, max_length=255)
    userId: str


class ProjectClass(BaseModel):
    """Schema for project class/category"""

    name: str
    color: str = Field(..., pattern=r"^#[0-9A-Fa-f]{6}$")
    description: str = ""


class TemplateReference(BaseModel):
    """Reference to a template"""

    id: str
    name: str
    fileType: str


class ProjectResponse(BaseModel):
    """Schema for project response"""

    id: str = Field(alias="_id")
    projectName: str
    templates: list[TemplateReference] = []
    classes: list[ProjectClass] = []
    general_pattern_description: str = ""

    class Config:
        populate_by_name = True


class ProjectDescriptionsUpdate(BaseModel):
    """Schema for updating project descriptions"""

    projectId: str
    generalDescription: str
    classDescriptions: list[dict[str, str]]


# ============================================================================
# Template Schemas
# ============================================================================


class TemplateCreate(BaseModel):
    """Schema for creating a new template"""

    templateName: str = Field(..., min_length=1, max_length=255)
    projectId: str
    fileType: str = Field(..., pattern=r"^\.(xlsx|xls|csv)$")


class TemplateUpdate(BaseModel):
    """Schema for updating a template"""

    request: dict[str, Any]
    projectId: str


class TemplateClone(BaseModel):
    """Schema for cloning a template"""

    newTemplateName: str = Field(..., min_length=1, max_length=255)
    projectId: str
    templateId: str


class ColumnInfo(BaseModel):
    """Information about a data column"""

    name: str
    index: int
    sampleData: str


class ExtractColumnsResponse(BaseModel):
    """Response for column extraction"""

    columns: list[ColumnInfo]


# ============================================================================
# Class Schemas
# ============================================================================


class ClassCreate(BaseModel):
    """Schema for creating a new class"""

    newClassName: str = Field(..., min_length=1, max_length=255)
    projectId: str
    newClassColor: str = Field(..., pattern=r"^#[0-9A-Fa-f]{6}$")
    description: str = ""


class ClassUpdate(BaseModel):
    """Schema for updating a class"""

    updatingClassName: str
    newClassName: str = Field(..., min_length=1, max_length=255)
    newClassColor: str = Field(..., pattern=r"^#[0-9A-Fa-f]{6}$")
    description: str = ""
    projectId: str


# ============================================================================
# Folder Schemas
# ============================================================================


class FolderCreate(BaseModel):
    """Schema for creating a new folder"""

    newFolderName: str = Field(..., min_length=1, max_length=255)
    project: IDReference
    template: IDReference
    userId: str


class FolderResponse(BaseModel):
    """Schema for folder response"""

    id: str = Field(alias="_id")
    name: str
    project: IDReference
    template: IDReference
    fileList: list[str] = []
    nbLabeledFiles: int = 0
    nbTotalFiles: int = 0

    class Config:
        populate_by_name = True


# ============================================================================
# File Schemas
# ============================================================================


class FileResponse(BaseModel):
    """Schema for file response"""

    id: str = Field(alias="_id")
    name: str
    parsing: str
    nbEvent: str
    description: str = ""
    rawPath: str = ""
    jsonPath: str = ""
    lastModifier: str
    lastUpdate: datetime
    label: str

    class Config:
        populate_by_name = True


class FileDescriptionUpdate(BaseModel):
    """Schema for updating file description"""

    file_id: str
    description: str


class ReparseFilesRequest(BaseModel):
    """Schema for requesting file reparsing"""

    folderId: str


# ============================================================================
# Label/Event Schemas
# ============================================================================


class EventData(BaseModel):
    """Schema for an event"""

    className: str
    color: str
    description: str = ""
    labeler: str
    start: float
    end: float
    hide: bool = False


class GuidelineData(BaseModel):
    """Schema for a guideline"""

    yaxis: str = "y"
    y: float
    channelName: str
    color: str = "#FF6B6B"
    hide: bool = False


class LabelUpdate(BaseModel):
    """Schema for updating a label"""

    label: dict[str, Any]
    user: str


class LabelResponse(BaseModel):
    """Schema for label response"""

    id: str = Field(alias="_id")
    events: list[EventData] = []
    guidelines: list[GuidelineData] = []

    class Config:
        populate_by_name = True


# ============================================================================
# User Schemas
# ============================================================================


class UserResponse(BaseModel):
    """Schema for user response"""

    id: str = Field(alias="_id")
    name: str
    mail: str
    activeSince: datetime
    projectList: list[str] = []
    folderList: list[str] = []
    assistantList: list[str] = []
    contributionHistory: list[dict] = []
    recent: list[dict] = []
    message: list[dict] = []
    badge: str = "Iron"
    rank: int = 100

    class Config:
        populate_by_name = True


class UserRecentFilesUpdate(BaseModel):
    """Schema for updating user recent files"""

    folderId: str
    fileId: str
    fileName: str
    folderName: str
    userInfo: dict[str, Any]


class UserSharedFolderUpdate(BaseModel):
    """Schema for sharing folder with user"""

    folder: dict[str, Any]
    user: dict[str, Any]
    userName: str
    message: str


class UserSharedProjectUpdate(BaseModel):
    """Schema for sharing project with user"""

    project: dict[str, Any]
    user: dict[str, Any]
    userName: str
    message: str


# ============================================================================
# Download Schemas
# ============================================================================


class DownloadRequest(BaseModel):
    """Schema for file download request"""

    projectId: str
    passwd: str


# ============================================================================
# Conversation/Chat Schemas
# ============================================================================


class ChatMessage(BaseModel):
    """Schema for a chat message"""

    role: str = Field(..., pattern="^(user|assistant)$")
    content: str
    timestamp: str


class ConversationResponse(BaseModel):
    """Schema for conversation response"""

    fileId: str
    history: list[dict] = []

