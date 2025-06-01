"""Base model class with common fields for all models."""

from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class BaseModel(SQLModel):
    """Base model class that all other models should inherit from.
    
    Provides common fields like id, created_at, and updated_at.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
        description="Timestamp when the record was created"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
        description="Timestamp when the record was last updated"
    )
