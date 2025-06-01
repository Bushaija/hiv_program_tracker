"""User related models: User, UserProfile, PasswordResetToken."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel
from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.geography import Province, District
    from app.models.facility import Facility


class User(BaseModel, table=True):
    """User model for authentication and basic user information."""
    __tablename__ = "users"

    # Override id from BaseModel to use UUID
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
        description="Unique identifier for the user"
    )
    full_name: str = Field(
        max_length=255,
        nullable=False,
        description="Full name of the user"
    )
    email: str = Field(
        max_length=255,
        unique=True,
        index=True,
        nullable=False,
        description="Email address of the user"
    )
    password_hash: str = Field(
        max_length=255,
        nullable=False,
        description="Hashed password for the user"
    )
    is_active: bool = Field(
        default=True,
        nullable=False,
        description="Whether the user account is active"
    )
    email_verified: bool = Field(
        default=False,
        nullable=False,
        description="Whether the user's email has been verified"
    )
    last_login_at: Optional[datetime] = Field(
        default=None,
        nullable=True,
        description="Timestamp of the user's last login"
    )

    # Relationships
    profile: Optional["UserProfile"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"uselist": False}  # One-to-one
    )
    # password_reset_tokens: List["PasswordResetToken"] = Relationship(back_populates="user") # If needed

    class Config:
        # BaseModel already includes created_at and updated_at
        # No need to redefine them here unless overriding behavior
        pass


class UserProfile(BaseModel, table=True):
    """UserProfile model storing additional user details and associations."""
    __tablename__ = "user_profiles"

    user_id: uuid.UUID = Field(
        foreign_key="users.id", 
        nullable=False, 
        unique=True, # Ensures one-to-one with User
        description="ID of the user this profile belongs to"
    )
    province_id: int = Field(
        foreign_key="provinces.id", 
        nullable=False, 
        description="ID of the province the user is associated with"
    )
    district_id: int = Field(
        foreign_key="districts.id", 
        nullable=False, 
        description="ID of the district the user is associated with"
    )
    facility_id: int = Field(
        foreign_key="facilities.id", 
        nullable=False, 
        description="ID of the facility the user is primarily associated with"
    )
    role: str = Field(
        default="accountant", 
        max_length=50, 
        nullable=False,
        description="Role of the user within the system (e.g., accountant, admin)"
    )

    # Relationships
    user: "User" = Relationship(back_populates="profile")
    province: "Province" = Relationship()
    district: "District" = Relationship()
    facility: "Facility" = Relationship()


class PasswordResetToken(BaseModel, table=True):
    """Model for storing password reset tokens."""
    __tablename__ = "password_reset_tokens"

    # Override id from BaseModel to use UUID for the token itself (or keep int if preferred for PK)
    # For this, let's assume the token value is the important part, and id is just a regular int PK.
    # If the token string itself should be the PK, this model needs adjustment.
    
    user_id: uuid.UUID = Field(
        foreign_key="users.id", 
        nullable=False,
        description="ID of the user this token belongs to"
    )
    token: str = Field(
        max_length=255, 
        unique=True, 
        index=True, 
        nullable=False,
        description="The password reset token string"
    )
    expires_at: datetime = Field(
        nullable=False,
        description="Timestamp when this token expires"
    )
    used_at: Optional[datetime] = Field(
        default=None,
        nullable=True,
        description="Timestamp when this token was used"
    )

    # Relationships
    user: "User" = Relationship()
    # Consider back_populates="password_reset_tokens" on User model if a list of tokens is needed there.
