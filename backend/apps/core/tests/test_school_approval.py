"""Tests for school approval workflow."""

import pytest
from django.utils import timezone
from django.core import mail
from rest_framework import status
from rest_framework.test import APIClient
from django_tenants.utils import schema_context
from apps.core.models import School
from apps.core.exceptions import (
    SchoolApprovalError,
    FreeTierLimitExceeded,
    EmailDeliveryError,
)
from apps.accounts.models import User


@pytest.fixture
def api_client():
    """Create a test API client."""
    from rest_framework.test import APIClient

    return APIClient()


@pytest.fixture
def superuser():
    """Create a superuser in public schema."""
    with schema_context("public"):
        return User.objects.create_superuser(
            username="admin", email="admin@example.com", password="testpass123"
        )


@pytest.fixture
def school():
    """Create a test school in public schema."""
    from django.db import connection
    from django_tenants.utils import get_public_schema_name
    import time

    # Ensure we're in public schema
    if connection.schema_name != get_public_schema_name():
        with schema_context(get_public_schema_name()):
            timestamp = str(int(time.time()))
            school = School.objects.create(
                name="Test School",
                schema_name=f"test_school_{timestamp}",
                address="Test Address",
                contact_email="test@school.com",
                contact_phone="1234567890",
                board_affiliation="CBSE",
                student_strength=100,
                staff_count=20,
                principal_name="Test Principal",
                principal_email="principal@test.com",
                principal_phone="1234567890",
                academic_year_start=4,
                academic_year_end=3,
                auto_create_schema=False,  # Don't create schema in tests
            )

            from apps.core.models import Domain

            Domain.objects.create(
                domain=f"test.{school.schema_name}.localhost",
                tenant=school,
                is_primary=True,
            )
            return school
    else:
        timestamp = str(int(time.time()))
        school = School.objects.create(
            name="Test School",
            schema_name=f"test_school_{timestamp}",
            address="Test Address",
            contact_email="test@school.com",
            contact_phone="1234567890",
            board_affiliation="CBSE",
            student_strength=100,
            staff_count=20,
            principal_name="Test Principal",
            principal_email="principal@test.com",
            principal_phone="1234567890",
            academic_year_start=4,
            academic_year_end=3,
            auto_create_schema=False,  # Don't create schema in tests
        )

        from apps.core.models import Domain

        Domain.objects.create(
            domain=f"test.{school.schema_name}.localhost",
            tenant=school,
            is_primary=True,
        )
        return school


@pytest.mark.django_db(transaction=True)
def test_approve_school(api_client, superuser, school):
    """Test school approval endpoint."""
    from django.db import connection
    from django_tenants.utils import get_public_schema_name

    # Ensure we're in public schema for approval
    if connection.schema_name != get_public_schema_name():
        with schema_context(get_public_schema_name()):
            api_client.force_authenticate(user=superuser)
            response = api_client.post(f"/api/v1/core/schools/{school.id}/approve/")

            assert response.status_code == status.HTTP_200_OK
            school.refresh_from_db()
            assert school.is_approved
            assert school.approval_date is not None

            # Check email was sent
            assert len(mail.outbox) == 1
            assert mail.outbox[0].to == [school.principal_email]
    else:
        api_client.force_authenticate(user=superuser)
        response = api_client.post(f"/api/v1/core/schools/{school.id}/approve/")

        assert response.status_code == status.HTTP_200_OK
        school.refresh_from_db()
        assert school.is_approved
        assert school.approval_date is not None

        # Check email was sent
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == [school.principal_email]


@pytest.mark.django_db(transaction=True)
def test_approve_school_unauthorized(api_client, school):
    """Test school approval endpoint without authentication."""
    with schema_context("public"):
        response = api_client.post(f"/api/v1/core/schools/{school.id}/approve/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db(transaction=True)
def test_approve_school_non_superuser(api_client, school):
    """Test school approval endpoint with non-superuser."""
    with schema_context("public"):
        user = User.objects.create_user(
            username="regular_user",
            email="user@example.com",
            password="testpass123",
            role="teacher",
        )
        api_client.force_authenticate(user=user)
        response = api_client.post(f"/api/v1/core/schools/{school.id}/approve/")
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db(transaction=True)
def test_approve_already_approved_school(api_client, superuser, school):
    """Test approving an already approved school."""
    with schema_context("public"):
        school.is_approved = True
        school.save()

        api_client.force_authenticate(user=superuser)
        response = api_client.post(f"/api/v1/core/schools/{school.id}/approve/")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db(transaction=True)
def test_free_tier_limits(api_client, superuser):
    """Test free tier limits during school creation."""
    with schema_context("public"):
        api_client.force_authenticate(user=superuser)

        # Test exceeding student limit
        with pytest.raises(FreeTierLimitExceeded):
            School.objects.create(
                name="Over Student Limit School",
                schema_name="over_limit_school",
                address="Test Address",
                contact_email="test@school.com",
                contact_phone="1234567890",
                principal_name="Test Principal",
                principal_email="principal@test.com",
                principal_phone="1234567890",
                student_strength=501,  # Exceeds limit
                staff_count=20,
                board_affiliation="CBSE",
            )

        # Test exceeding staff limit
        with pytest.raises(FreeTierLimitExceeded):
            School.objects.create(
                name="Over Staff Limit School",
                schema_name="staff_limit_school",
                address="Test Address",
                contact_email="test@school.com",
                contact_phone="1234567890",
                principal_name="Test Principal",
                principal_email="principal@test.com",
                principal_phone="1234567890",
                student_strength=100,
                staff_count=51,  # Exceeds limit
                board_affiliation="CBSE",
            )
