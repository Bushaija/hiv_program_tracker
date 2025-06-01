"""Geographic models for provinces and districts."""

from typing import List, Optional, TYPE_CHECKING
from sqlmodel import Field, Relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.facility import Facility


class Province(BaseModel, table=True):
    """Province model representing a geographic province/region."""
    __tablename__ = "provinces"

    name: str = Field(
        max_length=100,
        unique=True,
        nullable=False,
        description="Name of the province"
    )
    code: Optional[str] = Field(
        max_length=10,
        unique=True,
        description="Unique code for the province"
    )

    # Relationships
    districts: List["District"] = Relationship(
        back_populates="province",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class District(BaseModel, table=True):
    """District model representing an administrative district within a province."""
    __tablename__ = "districts"

    name: str = Field(
        max_length=100,
        nullable=False,
        description="Name of the district"
    )
    code: Optional[str] = Field(
        max_length=10,
        description="Unique code for the district"
    )
    province_id: int = Field(
        foreign_key="provinces.id",
        nullable=False,
        description="ID of the province this district belongs to"
    )

    # Relationships
    province: Province = Relationship(back_populates="districts")
    facilities: List["Facility"] = Relationship(back_populates="district")

    class Config:
        sa_relationship_kwargs = {
            "facilities": {"cascade": "all, delete-orphan"}
        }
