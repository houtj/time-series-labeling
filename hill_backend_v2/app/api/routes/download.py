"""Download-related API routes"""

import logging

from fastapi import APIRouter

from app.api.dependencies import DownloadServiceDep
from app.models.schemas import DownloadRequest

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/jsonfiles", tags=["download"])


@router.post("")
async def download_files(request: DownloadRequest, service: DownloadServiceDep):
    """Download JSON files for a project"""
    result = service.download_project_files(request.projectId, request.passwd)
    return result

