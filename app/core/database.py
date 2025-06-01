from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel
import logging

from app.core.config import get_database_url, settings
from app.models import *

logger = logging.getLogger(__name__)

# Create async engine
engine = create_async_engine(
    get_database_url(),
    echo=settings.ENVIRONMENT == "development",
    future=True,
    # Connection pool settings
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True,
    pool_recycle=300,
    # For testing with in-memory databases
    poolclass=StaticPool if "sqlite" in get_database_url() else None,
    connect_args={
        "check_same_thread": False
    } if "sqlite" in get_database_url() else {},
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function that yields db sessions.
    Use this in FastAPI dependencies.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database - create tables if they don't exist.
    This should be called during application startup.
    """
    try:
        # Import all models here to ensure they are registered with SQLModel
        from app.models.user import User, UserProfile, PasswordResetToken
        from app.models.geography import Province, District, Facility
        from app.models.program import Program, FiscalYear, ActivityCategory, ActivityType
        from app.models.planning import Plan, PlanActivity
        from app.models.execution import Execution, ExecutionItem
        from app.models.audit import AuditLog
        
        logger.info("Creating database tables...")
        
        async with engine.begin() as conn:
            # Create all tables
            await conn.run_sync(SQLModel.metadata.create_all)
            
        logger.info("Database tables created successfully")
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise


async def close_db() -> None:
    """
    Close database connections.
    This should be called during application shutdown.
    """
    try:
        await engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database: {e}")


# Database health check
async def check_db_health() -> bool:
    """
    Check if database is accessible.
    Returns True if healthy, False otherwise.
    """
    try:
        async with AsyncSessionLocal() as session:
            # Simple query to check connection
            result = await session.execute("SELECT 1")
            return result.scalar() == 1
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


# Transaction decorator for service layer
from functools import wraps
from typing import Callable, Any


def transactional(func: Callable) -> Callable:
    """
    Decorator to wrap service methods in database transactions.
    Automatically commits on success, rolls back on exception.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        # Check if session is already provided in kwargs
        if 'session' in kwargs and kwargs['session'] is not None:
            # Session already provided, don't create new transaction
            return await func(*args, **kwargs)
        
        # Create new session and transaction
        async with AsyncSessionLocal() as session:
            try:
                kwargs['session'] = session
                result = await func(*args, **kwargs)
                await session.commit()
                return result
            except Exception as e:
                await session.rollback()
                logger.error(f"Transaction rolled back due to error: {e}")
                raise
    
    return wrapper


# Session context manager for manual transaction control
class DatabaseSession:
    """
    Context manager for manual database session control.
    
    Usage:
    async with DatabaseSession() as session:
        # Your database operations
        user = await session.get(User, user_id)
        # Automatically commits on success, rolls back on exception
    """
    
    def __init__(self):
        self.session: AsyncSession = None
    
    async def __aenter__(self) -> AsyncSession:
        self.session = AsyncSessionLocal()
        return self.session
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            await self.session.rollback()
            logger.error(f"Database session rolled back due to: {exc_val}")
        else:
            await self.session.commit()
        
        await self.session.close()


# Utility functions for common database operations
async def get_or_create(session: AsyncSession, model, **kwargs):
    """
    Get an instance or create it if it doesn't exist.
    Returns (instance, created) tuple.
    """
    from sqlmodel import select
    
    # Try to get existing instance
    stmt = select(model).filter_by(**kwargs)
    result = await session.execute(stmt)
    instance = result.scalar_one_or_none()
    
    if instance:
        return instance, False
    
    # Create new instance
    instance = model(**kwargs)
    session.add(instance)
    await session.flush()  # Flush to get the ID
    return instance, True


async def bulk_insert_or_update(session: AsyncSession, model, data_list: list, update_on_conflict=True):
    """
    Bulk insert or update records.
    """
    if not data_list:
        return []
    
    instances = []
    for data in data_list:
        if isinstance(data, dict):
            instance = model(**data)
        else:
            instance = data
        instances.append(instance)
    
    session.add_all(instances)
    await session.flush()
    return instances