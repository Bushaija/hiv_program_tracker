"""Program and activity management models."""

from datetime import date
from typing import List, Optional, TYPE_CHECKING
from sqlmodel import Field, Relationship, SQLModel
from sqlalchemy import Column, Date, CheckConstraint, ARRAY, String

from app.models.base import BaseModel
from app.models.associations import FacilityProgram

if TYPE_CHECKING:
    from app.models.facility import Facility


class FiscalYear(BaseModel, table=True):
    """Fiscal year model for financial planning."""
    __tablename__ = "fiscal_years"

    name: str = Field(
        max_length=20,
        unique=True,
        nullable=False,
        description="Name of the fiscal year (e.g., '2023-2024')"
    )
    start_date: date = Field(
        nullable=False,
        description="Start date of the fiscal year"
    )
    end_date: date = Field(
        sa_column=Column(
            Date,
            CheckConstraint(
                "end_date > start_date",
                name="fiscal_year_date_check"
            ),
            nullable=False
        ),
        description="End date of the fiscal year"
    )
    is_current: bool = Field(
        default=False,
        description="Whether this is the current fiscal year"
    )
    is_active: bool = Field(
        default=True,
        description="Whether the fiscal year is active"
    )


class Program(BaseModel, table=True):
    """Program model representing a healthcare program."""
    __tablename__ = "programs"

    name: str = Field(
        max_length=100,
        unique=True,
        nullable=False,
        description="Name of the program"
    )
    code: str = Field(
        max_length=10,
        unique=True,
        nullable=False,
        description="Unique code for the program"
    )
    description: Optional[str] = Field(
        default=None,
        description="Description of the program"
    )
    is_active: bool = Field(
        default=True,
        description="Whether the program is currently active"
    )

    # Relationships
    facilities: List["Facility"] = Relationship(
        back_populates="programs",
        link_model=FacilityProgram
    )
    activity_categories: List["ActivityCategory"] = Relationship(
        back_populates="program",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class ActivityCategory(BaseModel, table=True):
    """Activity category model for grouping activities."""
    __tablename__ = "activity_categories"

    name: str = Field(
        max_length=200,
        nullable=False,
        description="Name of the activity category"
    )
    code: str = Field(
        max_length=20,
        nullable=False,
        description="Unique code for the category"
    )
    description: Optional[str] = Field(
        default=None,
        description="Description of the category"
    )
    facility_types: List[str] = Field(
        sa_column=Column(
            ARRAY(String(20)),
            nullable=False,
            server_default="{hospital,health_center}"
        ),
        description="Types of facilities this category applies to"
    )
    program_id: int = Field(
        foreign_key="programs.id",
        nullable=False,
        description="ID of the program this category belongs to"
    )
    is_active: bool = Field(
        default=True,
        description="Whether the category is currently active"
    )

    # Relationships
    program: Program = Relationship(back_populates="activity_categories")
    activity_types: List["ActivityType"] = Relationship(
        back_populates="category",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

    class Config:
        sa_relationship_kwargs = {
            "activity_types": {"cascade": "all, delete-orphan"}
        }


class ActivityType(BaseModel, table=True):
    """Activity type model for specific activities."""
    __tablename__ = "activity_types"

    name: str = Field(
        max_length=200,
        nullable=False,
        description="Name of the activity type"
    )
    code: str = Field(
        max_length=50,
        nullable=False,
        description="Code for the activity type"
    )
    description: Optional[str] = Field(
        default=None,
        description="Description of the activity type"
    )
    category_id: int = Field(
        foreign_key="activity_categories.id",
        nullable=False,
        description="ID of the category this activity type belongs to"
    )
    facility_types: List[str] = Field(
        sa_column=Column(
            ARRAY(String(20)),
            nullable=False,
            server_default="{hospital,health_center}"
        ),
        description="Types of facilities this activity applies to"
    )
    is_active: bool = Field(
        default=True,
        description="Whether the activity type is currently active"
    )

    # Relationships
    category: ActivityCategory = Relationship(back_populates="activity_types")

    class Config:
        sa_relationship_kwargs = {
            "category": {"lazy": "joined"}
        }
