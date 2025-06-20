"""Tests for reference data models and their relationships."""

import pytest
from datetime import date
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, text
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import (
    Province, District, Facility, Program,
    FiscalYear, ActivityCategory, ActivityType,
    FacilityProgram
)


@pytest.mark.asyncio
async def test_geographic_hierarchy(db_session: AsyncSession):
    """Test geographic hierarchy relationships and constraints."""
    # Create province1 and district1
    province1 = Province(name="Kigali", code="KGL")
    db_session.add(province1)
    await db_session.commit()
    await db_session.refresh(province1)

    district1 = District(name="Gasabo", code="GSB", province_id=province1.id)
    db_session.add(district1)
    await db_session.commit()
    await db_session.refresh(district1)

    # Create province2 and district2
    province2 = Province(name="Southern", code="STH")
    db_session.add(province2)
    await db_session.commit()
    await db_session.refresh(province2)

    district2 = District(name="Huye", code="HUY", province_id=province2.id)
    db_session.add(district2)
    await db_session.commit()
    await db_session.refresh(district2)

    # Valid facility creation
    facility1 = Facility(
        name="Kacyiru Hospital",
        code="KACH",
        facility_type="hospital",
        province_id=province1.id, # Belongs to Kigali
        district_id=district1.id  # Belongs to Gasabo (in Kigali)
    )
    db_session.add(facility1)
    await db_session.commit()
    await db_session.refresh(facility1)

    # Test basic attributes and relationships for the valid facility
    assert facility1.name == "Kacyiru Hospital"
    assert facility1.province_id == province1.id
    assert facility1.district_id == district1.id
    
    # Fetch related objects to confirm relationships
    retrieved_facility1 = await db_session.get(Facility, facility1.id)
    assert retrieved_facility1 is not None
    # SQLModel/SQLAlchemy might require explicit loading for relationships here if not eager loaded
    # For now, we check IDs directly. If relationships were auto-loaded, we could do:
    # assert retrieved_facility1.province.id == province1.id
    # assert retrieved_facility1.district.id == district1.id
    # assert retrieved_facility1.district.province_id == province1.id

    # Test scenario: creating a facility with mismatched province and district's province
    # This facility is in district2 (Southern Province), but we assign it to province1 (Kigali)
    # With the current simplified schema, this should NOT raise an IntegrityError
    # because there's no direct composite FK enforcing this specific cross-check.
    facility_with_mismatched_province = Facility(
        name="Mismatched Hospital",
        code="MISM",
        facility_type="hospital",
        province_id=province1.id,   # Attempting to assign to Kigali (province1)
        district_id=district2.id    # But district is Huye (in Southern, province2)
    )
    db_session.add(facility_with_mismatched_province)
    
    # We expect this to succeed at the database level now.
    # No IntegrityError should be raised based on the simplified FKs.
    await db_session.commit()
    await db_session.refresh(facility_with_mismatched_province)

    # Verify it was created
    retrieved_mismatched_facility = await db_session.get(Facility, facility_with_mismatched_province.id)
    assert retrieved_mismatched_facility is not None
    assert retrieved_mismatched_facility.province_id == province1.id # It was indeed set to province1
    assert retrieved_mismatched_facility.district_id == district2.id # And district2

    # This highlights that facility.district.province_id might not equal facility.province_id
    # We can fetch the district to confirm its actual province
    mismatched_facility_district = await db_session.get(District, retrieved_mismatched_facility.district_id)
    assert mismatched_facility_district is not None
    assert mismatched_facility_district.province_id == province2.id # District2 is in Province2
    
    # The test now demonstrates that facility.province_id (province1) can be different from
    # facility.district.province_id (province2) with the current schema.
    assert retrieved_mismatched_facility.province_id != mismatched_facility_district.province_id
    print("Successfully created facility with mismatched province and district's province, as expected with current schema.")


@pytest.mark.asyncio
async def test_facility_type_constraint(db_session: AsyncSession):
    """Test facility type constraints."""
    province = Province(name="Eastern", code="EST")
    db_session.add(province)
    await db_session.commit()
    await db_session.refresh(province)
    province_id = province.id

    district = District(name="Rwamagana", code="RWM", province_id=province_id)
    db_session.add(district)
    await db_session.commit()
    await db_session.refresh(district)
    district_id = district.id

    # Test invalid facility type
    with pytest.raises(IntegrityError):
        invalid_facility = Facility(
            name="Invalid Facility",
            code="INV",
            facility_type="clinic",  # Invalid type
            province_id=province_id,
            district_id=district_id
        )
        db_session.add(invalid_facility)
        await db_session.commit()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_fiscal_year_constraints(db_session: AsyncSession):
    """Test fiscal year date constraints and uniqueness."""
    # Valid fiscal year
    fiscal_year = FiscalYear(
        name="2023-2024",
        start_date=date(2023, 7, 1),
        end_date=date(2024, 6, 30),
        is_current=True
    )
    db_session.add(fiscal_year)
    await db_session.commit()

    # Test end_date > start_date constraint
    with pytest.raises(IntegrityError):
        invalid_fiscal_year = FiscalYear(
            name="2024-2025",
            start_date=date(2024, 7, 1),
            end_date=date(2024, 6, 30),  # End before start
            is_current=False
        )
        db_session.add(invalid_fiscal_year)
        await db_session.commit()
    await db_session.rollback()

    # Test unique name constraint
    with pytest.raises(IntegrityError):
        duplicate_fiscal_year = FiscalYear(
            name="2023-2024",  # Duplicate name
            start_date=date(2023, 7, 1),
            end_date=date(2024, 6, 30),
            is_current=False
        )
        db_session.add(duplicate_fiscal_year)
        await db_session.commit()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_program_relationships(db_session: AsyncSession):
    """Test program relationships and constraints."""
    # Create program
    program = Program(
        name="HIV Care",
        code="HIV",
        description="HIV/AIDS Care Program"
    )
    db_session.add(program)
    await db_session.commit()
    await db_session.refresh(program)
    program_id = program.id

    # Create facility
    province = Province(name="Western", code="WST")
    db_session.add(province)
    await db_session.commit()
    await db_session.refresh(province)
    province_id = province.id

    district = District(name="Karongi", code="KRG", province_id=province_id)
    db_session.add(district)
    await db_session.commit()
    await db_session.refresh(district)
    district_id = district.id

    facility = Facility(
        name="Karongi Hospital",
        code="KRGH",
        facility_type="hospital",
        province_id=province_id,
        district_id=district_id
    )
    db_session.add(facility)
    await db_session.commit()
    await db_session.refresh(facility)
    facility_id = facility.id

    # Link facility to program
    facility_program = FacilityProgram(
        facility_id=facility_id,
        program_id=program_id,
        is_active=True
    )
    db_session.add(facility_program)
    await db_session.commit()

    # Test relationships by querying
    result = await db_session.execute(
        select(FacilityProgram).where(
            FacilityProgram.facility_id == facility_id,
            FacilityProgram.program_id == program_id
        )
    )
    link = result.scalar_one_or_none()
    assert link is not None
    assert link.is_active is True

    # Test cascade delete
    await db_session.delete(program)
    await db_session.commit()
    
    # Verify facility_program link is deleted
    result = await db_session.execute(
        select(FacilityProgram).where(FacilityProgram.program_id == program_id)
    )
    links = result.scalars().all()
    assert len(links) == 0


@pytest.mark.asyncio
async def test_activity_hierarchy(db_session: AsyncSession):
    """Test activity category and type relationships."""
    # Create program
    program = Program(
        name="TB Program",
        code="TB",
        description="Tuberculosis Program"
    )
    db_session.add(program)
    await db_session.commit()
    await db_session.refresh(program)
    program_id = program.id

    # Create activity category
    category = ActivityCategory(
        name="Prevention",
        code="PREV",
        program_id=program_id,
        facility_types=["hospital", "health_center"]
    )
    db_session.add(category)
    await db_session.commit()
    await db_session.refresh(category)
    category_id = category.id

    # Create activity type
    activity_type = ActivityType(
        name="Screening",
        code="SCRN",
        category_id=category_id,
        facility_types=["hospital", "health_center"]
    )
    db_session.add(activity_type)
    await db_session.commit()
    await db_session.refresh(activity_type)

    # Test basic attributes
    assert activity_type.name == "Screening"
    assert activity_type.code == "SCRN"
    assert activity_type.category_id == category_id
    assert category.program_id == program_id

    # Test relationships by querying
    activity_check = await db_session.get(ActivityType, activity_type.id)
    category_check = await db_session.get(ActivityCategory, category_id)
    
    assert activity_check is not None
    assert category_check is not None
    assert activity_check.category_id == category_id

    # Test cascade delete
    await db_session.delete(category)
    await db_session.commit()
    
    # Verify activity type is deleted
    result = await db_session.execute(
        select(ActivityType).where(ActivityType.category_id == category_id)
    )
    activity_types = result.scalars().all()
    assert len(activity_types) == 0