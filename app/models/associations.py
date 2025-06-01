"""Association models for many-to-many relationships."""

from typing import Optional
from sqlmodel import SQLModel, Field


class FacilityProgram(SQLModel, table=True):
    """Association table for facility-program many-to-many relationship."""
    __tablename__ = "facility_programs"

    facility_id: Optional[int] = Field(
        default=None,
        foreign_key="facilities.id",
        primary_key=True
    )
    program_id: Optional[int] = Field(
        default=None,
        foreign_key="programs.id",
        primary_key=True
    )
    is_active: bool = Field(
        default=True,
        description="Whether the program is active for this facility"
    ) 