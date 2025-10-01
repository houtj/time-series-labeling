"""Database connection management with dependency injection"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import MongoClient
from pymongo.database import Database

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections for both sync and async operations"""

    def __init__(self):
        self.async_client: AsyncIOMotorClient | None = None
        self.sync_client: MongoClient | None = None
        self._settings = get_settings()

    async def connect_async(self) -> None:
        """Initialize async database connection"""
        logger.info("Connecting to MongoDB (async)...")
        self.async_client = AsyncIOMotorClient(self._settings.mongodb_url)
        # Test connection
        await self.async_client.admin.command("ping")
        logger.info("Successfully connected to MongoDB (async)")

    def connect_sync(self) -> None:
        """Initialize sync database connection"""
        logger.info("Connecting to MongoDB (sync)...")
        self.sync_client = MongoClient(self._settings.mongodb_url)
        # Test connection
        self.sync_client.admin.command("ping")
        logger.info("Successfully connected to MongoDB (sync)")

    async def disconnect_async(self) -> None:
        """Close async database connection"""
        if self.async_client:
            logger.info("Closing MongoDB connection (async)...")
            self.async_client.close()
            self.async_client = None

    def disconnect_sync(self) -> None:
        """Close sync database connection"""
        if self.sync_client:
            logger.info("Closing MongoDB connection (sync)...")
            self.sync_client.close()
            self.sync_client = None

    def get_async_db(self) -> AsyncIOMotorDatabase:
        """Get async database instance"""
        if not self.async_client:
            raise RuntimeError("Async database not connected")
        return self.async_client[self._settings.database_name]

    def get_sync_db(self) -> Database:
        """Get sync database instance"""
        if not self.sync_client:
            raise RuntimeError("Sync database not connected")
        return self.sync_client[self._settings.database_name]


# Global database manager instance
db_manager = DatabaseManager()


@asynccontextmanager
async def lifespan_manager():
    """Context manager for application lifespan"""
    # Startup
    await db_manager.connect_async()
    db_manager.connect_sync()
    yield
    # Shutdown
    await db_manager.disconnect_async()
    db_manager.disconnect_sync()


async def get_async_database() -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    """
    Dependency for getting async database instance
    
    Usage:
        @router.get("/endpoint")
        async def endpoint(db: AsyncIOMotorDatabase = Depends(get_async_database)):
            ...
    """
    yield db_manager.get_async_db()


def get_sync_database() -> Database:
    """
    Get sync database instance (for use in sync contexts like tools)
    
    Returns:
        Sync database instance
    """
    return db_manager.get_sync_db()


def get_data_folder_path() -> str:
    """Get configured data folder path"""
    return get_settings().data_folder_path

