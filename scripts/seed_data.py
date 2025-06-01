#!/usr/bin/env python3
"""
Database seeding script for Healthcare Planning System
Initializes the database with provinces, districts, facilities, and other essential data
"""

import asyncio
import json
import logging
from pathlib import Path
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models import Province, District

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get the path to the JSON data file
SCRIPT_DIR = Path(__file__).parent
DATA_FILE = SCRIPT_DIR / "province_district_hospitals.json"


async def get_db_session() -> AsyncSession:
    """Create database session."""
    engine = create_async_engine(str(settings.ASYNC_DATABASE_URL))
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session


async def seed_data() -> None:
    """Seed database with initial data."""
    try:
        # Load data from JSON file
        with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

        # Create database session
        engine = create_async_engine(str(settings.ASYNC_DATABASE_URL))
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        
        async with async_session() as session:
            # Create provinces and districts
            for province_data in data["provinces"]:
                # Create province
                province = Province(
                    name=province_data["name"],
                    code=province_data["code"]
                )
                session.add(province)
                await session.commit()
                await session.refresh(province)
                
                logger.info(f"Created province: {province.name}")

                # Create districts for this province
                for district_data in province_data["districts"]:
                    district = District(
                        name=district_data["name"],
                        code=district_data["code"],
                        province_id=province.id
                    )
                    session.add(district)
                    await session.commit()
                    logger.info(f"Created district: {district.name}")

        logger.info("Data seeding completed successfully")

    except Exception as e:
        logger.error(f"Error seeding data: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(seed_data())