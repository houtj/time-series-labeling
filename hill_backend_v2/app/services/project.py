"""Project service - Business logic for project operations"""

import logging
from typing import Any

from app.core.exceptions import NotFoundException
from app.repositories.project import ProjectRepository
from app.repositories.user import UserRepository

logger = logging.getLogger(__name__)


class ProjectService:
    """Service for project-related business logic"""

    def __init__(self, project_repo: ProjectRepository, user_repo: UserRepository):
        self.project_repo = project_repo
        self.user_repo = user_repo

    def create_project(self, project_name: str, user_id: str) -> dict[str, Any]:
        """
        Create a new project and add it to the user's project list
        
        Args:
            project_name: Name of the project
            user_id: ID of the user creating the project
            
        Returns:
            Created project data
            
        Raises:
            NotFoundException: If user not found
        """
        # Verify user exists
        user = self.user_repo.find_by_id(user_id)
        if not user:
            raise NotFoundException("User", user_id)

        # Create project
        new_project = {
            "projectName": project_name,
            "templates": [],
            "classes": [],
            "general_pattern_description": "",
        }

        project_id = self.project_repo.create(new_project)
        new_project["_id"] = project_id

        # Add project to user's list
        self.user_repo.add_project(user_id, project_id)

        logger.info(f"Created project {project_id} for user {user_id}")
        return new_project

    def get_projects(self, project_ids: list[str]) -> list[dict[str, Any]]:
        """Get multiple projects by IDs"""
        return self.project_repo.find_by_ids(project_ids)

    def add_class(self, project_id: str, class_data: dict[str, Any]) -> bool:
        """
        Add a class to a project
        
        Args:
            project_id: Project ID
            class_data: Class information (name, color, description)
            
        Returns:
            True if successful
            
        Raises:
            NotFoundException: If project not found
        """
        project = self.project_repo.find_by_id(project_id)
        if not project:
            raise NotFoundException("Project", project_id)

        success = self.project_repo.add_class(project_id, class_data)
        logger.info(f"Added class {class_data['name']} to project {project_id}")
        return success

    def update_class(
        self, project_id: str, old_class_name: str, new_class_data: dict[str, Any]
    ) -> bool:
        """
        Update a class in a project
        
        Args:
            project_id: Project ID
            old_class_name: Current class name
            new_class_data: Updated class information
            
        Returns:
            True if successful
            
        Raises:
            NotFoundException: If project not found
        """
        project = self.project_repo.find_by_id(project_id)
        if not project:
            raise NotFoundException("Project", project_id)

        success = self.project_repo.update_class(project_id, old_class_name, new_class_data)
        logger.info(f"Updated class {old_class_name} in project {project_id}")
        return success

    def update_descriptions(
        self, project_id: str, general_description: str, class_descriptions: list[dict]
    ) -> bool:
        """
        Update project and class descriptions
        
        Args:
            project_id: Project ID
            general_description: General pattern description
            class_descriptions: List of class descriptions
            
        Returns:
            True if successful
            
        Raises:
            NotFoundException: If project not found
        """
        project = self.project_repo.find_by_id(project_id)
        if not project:
            raise NotFoundException("Project", project_id)

        # Update general description
        self.project_repo.update_by_id(project_id, {"general_pattern_description": general_description})

        # Update class descriptions
        for class_desc in class_descriptions:
            self.project_repo.update_class_description(
                project_id, class_desc["name"], class_desc["description"]
            )

        logger.info(f"Updated descriptions for project {project_id}")
        return True

