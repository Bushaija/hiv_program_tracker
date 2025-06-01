"""Database initialization script."""
import asyncio
import logging
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def init_db() -> None:
    """Initialize database tables."""
    try:
        # Import all SQLModel models here
        from app.models import Province, District  # noqa

        # Create async engine
        engine = create_async_engine(str(settings.ASYNC_DATABASE_URL))

        # Create all tables
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.drop_all)
            await conn.run_sync(SQLModel.metadata.create_all)

        logger.info("Database tables created successfully")

    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(init_db())
