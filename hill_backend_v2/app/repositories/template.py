"""Template repository for database operations"""

from pymongo.database import Database

from app.repositories.base import BaseRepository


class TemplateRepository(BaseRepository):
    """Repository for template-related database operations"""

    def __init__(self, db: Database):
        super().__init__(db, "templates")

