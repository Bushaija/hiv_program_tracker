"""Facility model and related schemas."""

from typing import List, Optional, TYPE_CHECKING
from sqlmodel import Field, Relationship
from sqlalchemy import Column, String, CheckConstraint

from app.models.base import BaseModel
from app.models.associations import FacilityProgram

if TYPE_CHECKING:
    from app.models.geography import District, Province
    from app.models.program import Program


class Facility(BaseModel, table=True):
    """Facility model representing a healthcare facility."""
    __tablename__ = "facilities"

    name: str = Field(
        max_length=200,
        nullable=False,
        description="Name of the facility"
    )
    code: Optional[str] = Field(
        max_length=20,
        unique=True,
        description="Unique code for the facility"
    )
    facility_type: str = Field(
        sa_column=Column(
            String(20),
            CheckConstraint(
                "facility_type IN ('hospital', 'health_center')",
                name="facility_type_check"
            ),
            nullable=False
        ),
        description="Type of facility (hospital, health_center)"
    )
    is_active: bool = Field(
        default=True,
        description="Whether the facility is currently active"
    )

    # Geographic hierarchy
    province_id: int = Field(
        foreign_key="provinces.id",
        nullable=False,
        description="ID of the province this facility belongs to"
    )
    district_id: int = Field(
        foreign_key="districts.id",
        nullable=False,
        description="ID of the district this facility belongs to"
    )

    # Relationships - Remove lazy loading configurations that cause issues
    province: "Province" = Relationship(back_populates="facilities")
    district: "District" = Relationship(back_populates="facilities")
    programs: List["Program"] = Relationship(
        back_populates="facilities",
        link_model=FacilityProgram
    )