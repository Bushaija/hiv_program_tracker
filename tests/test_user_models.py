"""Tests for User Management models and their database interactions."""

import pytest
import uuid
from sqlalchemy.exc import IntegrityError
from sqlmodel import select # Ensure select is imported
from sqlalchemy.orm import selectinload # For eager loading
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import User, UserProfile, Province, District, Facility # Assuming these are in app.models
from app.core.security import get_password_hash # For creating a dummy password hash

@pytest.mark.asyncio
async def test_create_user_and_profile(db_session: AsyncSession):
    """Test creating a User and their associated UserProfile."""
    # 1. Create prerequisite geographic data
    province = Province(name=f"Test Province {uuid.uuid4()}", code=f"TP{uuid.uuid4().hex[:4]}")
    db_session.add(province)
    await db_session.commit()
    await db_session.refresh(province)
    province_id = province.id # Store ID after refresh

    district = District(name=f"Test District {uuid.uuid4()}", code=f"TD{uuid.uuid4().hex[:4]}", province_id=province_id)
    db_session.add(district)
    await db_session.commit()
    await db_session.refresh(district)
    district_id = district.id # Store ID after refresh

    facility = Facility(
        name=f"Test Facility {uuid.uuid4()}", 
        code=f"TF{uuid.uuid4().hex[:4]}", 
        facility_type="hospital",
        province_id=province_id,
        district_id=district_id
    )
    db_session.add(facility)
    await db_session.commit()
    await db_session.refresh(facility)
    facility_id = facility.id # Store ID after refresh

    # 2. Create a User
    user_email = f"testuser_{uuid.uuid4()}@example.com"
    hashed_password = get_password_hash("testpassword")
    
    new_user = User(
        full_name="Test User",
        email=user_email,
        password_hash=hashed_password,
        is_active=True,
        email_verified=True
    )
    db_session.add(new_user)
    await db_session.commit()
    await db_session.refresh(new_user)
    user_id = new_user.id # Store ID after refresh

    assert user_id is not None
    assert new_user.email == user_email

    # 3. Create a UserProfile linked to the User
    new_profile = UserProfile(
        user_id=user_id,
        province_id=province_id,
        district_id=district_id,
        facility_id=facility_id,
        role="test_role"
    )
    db_session.add(new_profile)
    await db_session.commit()
    await db_session.refresh(new_profile)
    profile_id = new_profile.id # Store ID after refresh

    assert profile_id is not None
    assert new_profile.user_id == user_id
    assert new_profile.role == "test_role"

    # 4. Verify the relationship explicitly by re-fetching with eager loading
    # Fetch User with its profile
    stmt_user = select(User).where(User.id == user_id).options(selectinload(User.profile))
    result_user = await db_session.exec(stmt_user)
    fetched_user_with_profile = result_user.one_or_none()

    assert fetched_user_with_profile is not None
    assert fetched_user_with_profile.profile is not None
    assert fetched_user_with_profile.profile.id == profile_id
    assert fetched_user_with_profile.profile.role == "test_role"

    # Fetch UserProfile with its user
    stmt_profile = select(UserProfile).where(UserProfile.id == profile_id).options(selectinload(UserProfile.user))
    result_profile = await db_session.exec(stmt_profile)
    fetched_profile_with_user = result_profile.one_or_none()

    assert fetched_profile_with_user is not None
    assert fetched_profile_with_user.user is not None
    assert fetched_profile_with_user.user.id == user_id
    assert fetched_profile_with_user.user.email == user_email

    # Test unique constraint on User.email
    with pytest.raises(IntegrityError):
        duplicate_user = User(
            full_name="Duplicate Test User",
            email=user_email, # Same email
            password_hash=get_password_hash("anotherpassword")
        )
        db_session.add(duplicate_user)
        await db_session.commit()
    await db_session.rollback() # Rollback the failed transaction

    # Test unique constraint on UserProfile.user_id
    # Create a new user first for this test to avoid FK issues with the previous user
    other_user_email = f"otheruser_{uuid.uuid4()}@example.com"
    other_user = User(full_name="Other User", email=other_user_email, password_hash=get_password_hash("pass"))
    db_session.add(other_user)
    await db_session.commit()
    await db_session.refresh(other_user)
    other_user_id = other_user.id

    with pytest.raises(IntegrityError):
        # This attempts to create a new profile for an existing user (user_id)
        # but UserProfile.user_id is already linked to new_profile.
        # However, the unique constraint is on UserProfile.user_id itself.
        # So, we are trying to create another UserProfile record with the *same user_id* as new_profile
        duplicate_profile = UserProfile(
            user_id=user_id, # Same user_id as new_profile, which should violate unique constraint
            province_id=province_id,
            district_id=district_id,
            facility_id=facility_id,
            role="another_role"
        )
        db_session.add(duplicate_profile)
        await db_session.commit()
    await db_session.rollback()

# We can add a test for PasswordResetToken later if needed. 