"""Label repository for database operations"""

from pymongo.database import Database

from app.repositories.base import BaseRepository


class LabelRepository(BaseRepository):
    """Repository for label-related database operations"""

    def __init__(self, db: Database):
        super().__init__(db, "labels")

