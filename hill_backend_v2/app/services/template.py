"""Template service - Business logic for template operations"""

import logging
from typing import Any

from app.core.exceptions import NotFoundException
from app.repositories.project import ProjectRepository
from app.repositories.template import TemplateRepository

logger = logging.getLogger(__name__)


class TemplateService:
    """Service for template-related business logic"""

    def __init__(self, template_repo: TemplateRepository, project_repo: ProjectRepository):
        self.template_repo = template_repo
        self.project_repo = project_repo

    def create_template(self, template_name: str, project_id: str, file_type: str) -> str:
        """
        Create a new template and add it to a project
        
        Args:
            template_name: Name of the template
            project_id: Project ID
            file_type: File type (.xlsx, .xls, .csv)
            
        Returns:
            Template ID
            
        Raises:
            NotFoundException: If project not found
        """
        # Verify project exists
        project = self.project_repo.find_by_id(project_id)
        if not project:
            raise NotFoundException("Project", project_id)

        # Create template
        new_template = {"templateName": template_name, "fileType": file_type, "channels": [], "x": {}}

        template_id = self.template_repo.create(new_template)

        # Add template to project
        self.project_repo.add_template(
            project_id, {"id": template_id, "name": template_name, "fileType": file_type}
        )

        logger.info(f"Created template {template_id} for project {project_id}")
        return template_id

    def get_template(self, template_id: str) -> dict[str, Any]:
        """
        Get template by ID
        
        Args:
            template_id: Template ID
            
        Returns:
            Template data
            
        Raises:
            NotFoundException: If template not found
        """
        template = self.template_repo.find_by_id(template_id)
        if not template:
            raise NotFoundException("Template", template_id)
        return template

    def update_template(self, template_id: str, project_id: str, template_data: dict) -> bool:
        """
        Update a template
        
        Args:
            template_id: Template ID
            project_id: Project ID
            template_data: Updated template data
            
        Returns:
            True if successful
            
        Raises:
            NotFoundException: If template not found
        """
        template = self.template_repo.find_by_id(template_id)
        if not template:
            raise NotFoundException("Template", template_id)

        # Convert integer fields
        if "headRow" in template_data:
            template_data["headRow"] = int(template_data["headRow"])
        if "skipRow" in template_data:
            template_data["skipRow"] = int(template_data["skipRow"])

        # Update template
        self.template_repo.update_by_id(template_id, template_data)

        # Update file type in project if present
        if "fileType" in template_data:
            self.project_repo.update_template_filetype(
                project_id, template_id, template_data["fileType"]
            )

        logger.info(f"Updated template {template_id}")
        return True

    def clone_template(self, template_id: str, new_name: str, project_id: str) -> str:
        """
        Clone an existing template
        
        Args:
            template_id: Template ID to clone
            new_name: Name for the cloned template
            project_id: Project ID
            
        Returns:
            New template ID
            
        Raises:
            NotFoundException: If template or project not found
        """
        # Get original template
        original = self.template_repo.find_by_id(template_id)
        if not original:
            raise NotFoundException("Template", template_id)

        # Verify project exists
        project = self.project_repo.find_by_id(project_id)
        if not project:
            raise NotFoundException("Project", project_id)

        # Clone template
        cloned = original.copy()
        del cloned["_id"]
        cloned["templateName"] = new_name

        new_template_id = self.template_repo.create(cloned)

        # Add to project
        self.project_repo.add_template(
            project_id,
            {"id": new_template_id, "name": new_name, "fileType": original["fileType"]},
        )

        logger.info(f"Cloned template {template_id} to {new_template_id}")
        return new_template_id

