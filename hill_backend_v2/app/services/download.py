"""Download service - Business logic for file downloads"""

import json
import logging
from pathlib import Path
from typing import Any

from bson.json_util import dumps

from app.core.config import get_settings
from app.core.exceptions import UnauthorizedException, NotFoundException
from app.repositories.file import FileRepository
from app.repositories.label import LabelRepository

logger = logging.getLogger(__name__)
settings = get_settings()


class DownloadService:
    """Service for download-related operations"""

    def __init__(self, file_repo: FileRepository, label_repo: LabelRepository):
        self.file_repo = file_repo
        self.label_repo = label_repo
        self.data_folder = Path(settings.data_folder_path)

    def download_project_files(self, project_id: str, password: str) -> dict[str, Any]:
        """
        Download all JSON files for a project
        
        Args:
            project_id: Project ID
            password: Download password
            
        Returns:
            Dictionary of file data
            
        Raises:
            UnauthorizedException: If password is incorrect
        """
        # Verify password
        if password != settings.download_api_password:
            raise UnauthorizedException("Incorrect password")

        project_folder = self.data_folder / project_id
        if not project_folder.exists():
            return {}

        json_response = {}

        # Iterate through file IDs in project folder
        for file_path in project_folder.iterdir():
            if not file_path.is_dir():
                continue

            file_id = file_path.name
            file_db = self.file_repo.find_by_id(file_id)

            if not file_db:
                continue

            # Get JSON data if available
            data = "none"
            if "jsonPath" in file_db and file_db["jsonPath"]:
                json_file_path = self.data_folder / file_db["jsonPath"]
                try:
                    with open(json_file_path, "r") as f:
                        data = json.load(f)
                except Exception as e:
                    logger.warning(f"Could not read JSON for file {file_id}: {e}")

            # Get label if available
            label = "none"
            if "label" in file_db and file_db["label"]:
                label_db = self.label_repo.find_by_id(file_db["label"])
                if label_db:
                    label = dumps(label_db)

            json_response[file_id] = {
                "name": file_db.get("name", ""),
                "data": data,
                "label": label,
            }

        logger.info(f"Downloaded {len(json_response)} files for project {project_id}")
        return json_response

