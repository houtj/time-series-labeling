"""Project repository for database operations"""

from bson import ObjectId
from pymongo.database import Database

from app.repositories.base import BaseRepository


class ProjectRepository(BaseRepository):
    """Repository for project-related database operations"""

    def __init__(self, db: Database):
        super().__init__(db, "projects")

    def add_template(self, project_id: str, template: dict) -> bool:
        """Add a template to a project"""
        return self.update_one(
            {"_id": ObjectId(project_id)}, {"$push": {"templates": template}}
        )

    def update_template_filetype(self, project_id: str, template_id: str, file_type: str) -> bool:
        """Update template file type in project"""
        return self.update_one(
            {"_id": ObjectId(project_id)},
            {"$set": {"templates.$[elem].fileType": file_type}},
            array_filters=[{"elem.id": template_id}],
        )

    def add_class(self, project_id: str, class_data: dict) -> bool:
        """Add a class to a project"""
        return self.update_one({"_id": ObjectId(project_id)}, {"$push": {"classes": class_data}})

    def update_class(self, project_id: str, old_class_name: str, new_class_data: dict) -> bool:
        """Update a class in a project"""
        return self.update_one(
            {"_id": ObjectId(project_id), "classes.name": old_class_name},
            {"$set": {"classes.$": new_class_data}},
        )

    def update_class_description(self, project_id: str, class_name: str, description: str) -> bool:
        """Update description for a specific class"""
        return self.update_one(
            {"_id": ObjectId(project_id), "classes.name": class_name},
            {"$set": {"classes.$.description": description}},
        )

