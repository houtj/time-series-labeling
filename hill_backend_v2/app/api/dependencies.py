"""Dependency injection for API routes"""

from typing import Annotated

from fastapi import Depends
from pymongo.database import Database

from app.core.database import get_sync_database
from app.repositories.conversation import ConversationRepository
from app.repositories.file import FileRepository
from app.repositories.folder import FolderRepository
from app.repositories.label import LabelRepository
from app.repositories.project import ProjectRepository
from app.repositories.template import TemplateRepository
from app.repositories.user import UserRepository
from app.services.download import DownloadService
from app.services.extraction import ExtractionService
from app.services.file import FileService
from app.services.folder import FolderService
from app.services.label import LabelService
from app.services.project import ProjectService
from app.services.template import TemplateService
from app.services.user import UserService


# Database dependency
def get_db() -> Database:
    """Get database instance"""
    return get_sync_database()


DatabaseDep = Annotated[Database, Depends(get_db)]


# Repository dependencies
def get_project_repo(db: DatabaseDep) -> ProjectRepository:
    return ProjectRepository(db)


def get_template_repo(db: DatabaseDep) -> TemplateRepository:
    return TemplateRepository(db)


def get_folder_repo(db: DatabaseDep) -> FolderRepository:
    return FolderRepository(db)


def get_file_repo(db: DatabaseDep) -> FileRepository:
    return FileRepository(db)


def get_label_repo(db: DatabaseDep) -> LabelRepository:
    return LabelRepository(db)


def get_user_repo(db: DatabaseDep) -> UserRepository:
    return UserRepository(db)


def get_conversation_repo(db: DatabaseDep) -> ConversationRepository:
    return ConversationRepository(db)


# Service dependencies
def get_project_service(
    project_repo: Annotated[ProjectRepository, Depends(get_project_repo)],
    user_repo: Annotated[UserRepository, Depends(get_user_repo)],
) -> ProjectService:
    return ProjectService(project_repo, user_repo)


def get_template_service(
    template_repo: Annotated[TemplateRepository, Depends(get_template_repo)],
    project_repo: Annotated[ProjectRepository, Depends(get_project_repo)],
) -> TemplateService:
    return TemplateService(template_repo, project_repo)


def get_folder_service(
    folder_repo: Annotated[FolderRepository, Depends(get_folder_repo)],
    user_repo: Annotated[UserRepository, Depends(get_user_repo)],
    file_repo: Annotated[FileRepository, Depends(get_file_repo)],
    label_repo: Annotated[LabelRepository, Depends(get_label_repo)],
) -> FolderService:
    return FolderService(folder_repo, user_repo, file_repo, label_repo)


def get_file_service(
    file_repo: Annotated[FileRepository, Depends(get_file_repo)],
    label_repo: Annotated[LabelRepository, Depends(get_label_repo)],
    folder_repo: Annotated[FolderRepository, Depends(get_folder_repo)],
) -> FileService:
    return FileService(file_repo, label_repo, folder_repo)


def get_label_service(
    label_repo: Annotated[LabelRepository, Depends(get_label_repo)],
    file_repo: Annotated[FileRepository, Depends(get_file_repo)],
    folder_repo: Annotated[FolderRepository, Depends(get_folder_repo)],
) -> LabelService:
    return LabelService(label_repo, file_repo, folder_repo)


def get_user_service(
    user_repo: Annotated[UserRepository, Depends(get_user_repo)],
) -> UserService:
    return UserService(user_repo)


def get_download_service(
    file_repo: Annotated[FileRepository, Depends(get_file_repo)],
    label_repo: Annotated[LabelRepository, Depends(get_label_repo)],
) -> DownloadService:
    return DownloadService(file_repo, label_repo)


def get_extraction_service(
    template_repo: Annotated[TemplateRepository, Depends(get_template_repo)],
) -> ExtractionService:
    return ExtractionService(template_repo)


# Typed service dependencies for use in routes
ProjectServiceDep = Annotated[ProjectService, Depends(get_project_service)]
TemplateServiceDep = Annotated[TemplateService, Depends(get_template_service)]
FolderServiceDep = Annotated[FolderService, Depends(get_folder_service)]
FileServiceDep = Annotated[FileService, Depends(get_file_service)]
LabelServiceDep = Annotated[LabelService, Depends(get_label_service)]
UserServiceDep = Annotated[UserService, Depends(get_user_service)]
DownloadServiceDep = Annotated[DownloadService, Depends(get_download_service)]
ExtractionServiceDep = Annotated[ExtractionService, Depends(get_extraction_service)]

