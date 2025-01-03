import pytest
from django.urls import reverse
from rest_framework import status
from django_tenants.test.client import TenantClient
from apps.accounts.models import User, StudentProfile
from apps.core.models import School, Domain
from django_tenants.utils import schema_context

# Use the tenant-aware API client from conftest.py directly

# Use the tenant fixture directly as the test school


@pytest.fixture
def test_admin(tenant):
    with schema_context(tenant.schema_name):
        admin = User.objects.create_user(
            username="admin",
            email="admin@test.com",
            password="testpass123",
            role="school_admin",
            school=tenant,
        )
        return admin


@pytest.mark.django_db(transaction=True)
@pytest.mark.tenant
class TestStudents:
    @pytest.mark.django_db(transaction=True)
    def test_create_student(self, api_client, tenant, test_admin):
        """Test creating a new student with proper school association."""
        with schema_context(tenant.schema_name):
            api_client.force_authenticate(user=test_admin)
            import time

            timestamp = str(int(time.time()))
            url = "/api/v1/accounts/students/"
            data = {
                "username": f"student1_{timestamp}",
                "email": f"student1_{timestamp}@test.com",
                "password": "testpass123",
                "first_name": "Test",
                "last_name": "Student",
                "role": "student",
                "school": tenant.id,
                "admission_number": "ADM001",
                "date_of_birth": "2010-01-01",
                "gender": "M",
                "blood_group": "O+",
                "address": "123 Student St",
                "parent_name": "Parent Name",
                "parent_phone": "1234567890",
                "parent_email": "parent@test.com",
            }

            response = api_client.post(url, data)
            assert response.status_code == status.HTTP_201_CREATED
            assert User.objects.filter(role="student").count() == 1
            assert StudentProfile.objects.count() == 1
            student = User.objects.get(username=f"student1_{timestamp}")
            assert student.studentprofile.admission_number == "ADM001"
            assert student.school_id == tenant.id

    @pytest.mark.django_db(transaction=True)
    def test_list_students(self, api_client, tenant, test_admin):
        with schema_context(tenant.schema_name):
            api_client.force_authenticate(user=test_admin)

            # Create multiple students
            for i in range(3):
                user = User.objects.create_user(
                    username=f"student{i}",
                    email=f"student{i}@test.com",
                    password="testpass123",
                    role="student",
                    school=tenant,
                )
                StudentProfile.objects.create(
                    user=user,
                    admission_number=f"ADM00{i}",
                    date_of_birth="2010-01-01",
                    gender="M",
                    blood_group="O+",
                    address="123 Student St",
                    parent_name="Parent Name",
                    parent_phone="1234567890",
                    parent_email=f"parent{i}@test.com",
                )

            url = "/api/v1/accounts/students/"
            response = api_client.get(url)
            assert response.status_code == status.HTTP_200_OK
            assert response.data["count"] == 3
            assert len(response.data["results"]) == 3

    @pytest.mark.django_db(transaction=True)
    def test_update_student(self, api_client, tenant, test_admin):
        with schema_context(tenant.schema_name):
            api_client.force_authenticate(user=test_admin)

            # Create a student
            import time

            timestamp = str(int(time.time()))
            user = User.objects.create_user(
                username=f"student1_{timestamp}",
                email=f"student1_{timestamp}@test.com",
                password="testpass123",
                role="student",
                school=tenant,
            )
            profile = StudentProfile.objects.create(
                user=user,
                admission_number="ADM001",
                date_of_birth="2010-01-01",
                gender="M",
                blood_group="O+",
                address="123 Student St",
                parent_name="Parent Name",
                parent_phone="1234567890",
                parent_email=f"parent_{timestamp}@test.com",
            )

            url = f"/api/v1/accounts/manage-students/{user.pk}/"
            data = {
                "first_name": "Updated",
                "last_name": "Student",
                "admission_number": "ADM001",
                "date_of_birth": "2010-01-01",
                "gender": "M",
                "blood_group": "A+",
                "address": "Updated Address",
                "parent_name": "Updated Parent",
                "parent_phone": "0987654321",
                "parent_email": "updatedparent@test.com",
            }
            response = api_client.put(url, data)
            assert response.status_code == status.HTTP_200_OK
            profile.refresh_from_db()
            assert profile.blood_group == "A+"
            assert profile.parent_name == "Updated Parent"

    @pytest.mark.django_db(transaction=True)
    def test_delete_student(self, api_client, tenant, test_admin):
        with schema_context(tenant.schema_name):
            api_client.force_authenticate(user=test_admin)

            # Create a student
            import time

            timestamp = str(int(time.time()))
            user = User.objects.create_user(
                username=f"student1_{timestamp}",
                email=f"student1_{timestamp}@test.com",
                password="testpass123",
                role="student",
                school=tenant,
            )
            StudentProfile.objects.create(
                user=user,
                admission_number="ADM001",
                date_of_birth="2010-01-01",
                gender="M",
                blood_group="O+",
                address="123 Student St",
                parent_name="Parent Name",
                parent_phone="1234567890",
                parent_email=f"parent_{timestamp}@test.com",
            )

            url = f"/api/v1/accounts/manage-students/{user.pk}/"
            response = api_client.delete(url)
            assert response.status_code == status.HTTP_204_NO_CONTENT
            assert User.objects.filter(role="student").count() == 0
            assert StudentProfile.objects.count() == 0
