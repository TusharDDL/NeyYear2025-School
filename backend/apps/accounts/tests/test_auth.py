import pytest
from django.urls import reverse
from rest_framework import status
from django_tenants.test.client import TenantClient
from apps.accounts.models import User
from apps.core.models import School, Domain
from django_tenants.utils import schema_context

# Using fixtures from conftest.py


@pytest.mark.django_db(transaction=True)
@pytest.mark.tenant
class TestAuthentication:
    def test_user_registration(self, api_client, tenant):
        """Test user registration with proper tenant context."""
        with schema_context("public"):
            tenant.is_approved = True
            tenant.save()

        with schema_context(tenant.schema_name):
            import time

            timestamp = str(int(time.time()))
            url = "/api/v1/accounts/users/"  # Use absolute URL path
            data = {
                "username": f"testuser_{timestamp}",
                "email": f"test_{timestamp}@example.com",
                "password": "testpass123",
                "role": "teacher",
                "first_name": "Test",
                "last_name": "User",
            }
            response = api_client.post(url, data, format="json")
            assert response.status_code == status.HTTP_201_CREATED
            assert User.objects.count() == 1
            user = User.objects.get(username=f"testuser_{timestamp}")
            assert user.email == f"test_{timestamp}@example.com"
            assert user.role == "teacher"
            assert user.school_id == tenant.id

    def test_user_login(self, api_client, tenant):
        with schema_context(tenant.schema_name):
            # Create a user first
            import time

            timestamp = str(int(time.time()))
            user = User.objects.create_user(
                username=f"testuser_{timestamp}",
                email=f"test_{timestamp}@example.com",
                password="testpass123",
                role="teacher",
                school=tenant,
            )

            url = "/api/v1/accounts/token/"
            data = {"username": f"testuser_{timestamp}", "password": "testpass123"}
            response = api_client.post(url, data, format="json")
            assert response.status_code == status.HTTP_200_OK
            assert "access" in response.data
            assert "refresh" in response.data

    def test_token_refresh(self, api_client, tenant):
        with schema_context(tenant.schema_name):
            # Create a user and get initial tokens
            user = User.objects.create_user(
                username="testuser",
                email="test@example.com",
                password="testpass123",
                role="teacher",
                school=tenant,
            )

            # Get initial tokens
            url = "/api/v1/accounts/token/"
            response = api_client.post(
                url, {"username": "testuser", "password": "testpass123"}
            )
            refresh_token = response.data["refresh"]

            # Try to refresh the token
            url = "/api/v1/accounts/token/refresh/"
            response = api_client.post(url, {"refresh": refresh_token})
            assert response.status_code == status.HTTP_200_OK
            assert "access" in response.data

    def test_invalid_login(self, api_client, tenant):
        with schema_context(tenant.schema_name):
            url = "/api/v1/accounts/token/"
            data = {"username": "nonexistent", "password": "wrongpass"}
            response = api_client.post(url, data)
            assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_password_change(self, api_client, tenant):
        with schema_context(tenant.schema_name):
            user = User.objects.create_user(
                username="testuser",
                email="test@example.com",
                password="testpass123",
                role="teacher",
                school=tenant,
            )

            # Login first
            api_client.force_authenticate(user=user)

            url = f"/api/v1/accounts/users/{user.id}/change-password/"
            data = {"old_password": "testpass123", "new_password": "newtestpass123"}
            response = api_client.post(url, data)
            assert response.status_code == status.HTTP_200_OK

            # Verify new password works
            url = "/api/v1/accounts/token/"
            data = {"username": "testuser", "password": "newtestpass123"}
            response = api_client.post(url, data)
            assert response.status_code == status.HTTP_200_OK
