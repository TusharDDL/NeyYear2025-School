import pytest
from django.urls import reverse
from rest_framework import status
from django_tenants.test.client import TenantClient
from django.db import transaction
from apps.library.models import Book, BookIssue
from apps.accounts.models import User
from apps.core.models import School, Domain
from django_tenants.utils import schema_context
from datetime import datetime, timedelta

# Using fixtures from conftest.py

@pytest.fixture
def test_librarian(tenant):
    with schema_context(tenant.schema_name):
        librarian = User.objects.create_user(
            username='librarian',
            email='librarian@test.com',
            password='testpass123',
            role='librarian',
            school=tenant
        )
        return librarian

@pytest.fixture
def test_student(tenant):
    with schema_context(tenant.schema_name):
        student = User.objects.create_user(
            username='student',
            email='student@test.com',
            password='testpass123',
            role='student',
            school=tenant
        )
        return student

@pytest.mark.django_db(transaction=True)
class TestLibrary:
    @pytest.mark.django_db(transaction=True)
    def test_add_book(self, api_client, tenant, test_librarian):
        """Test adding a book with proper tenant context."""
        with schema_context(tenant.schema_name):
            api_client.force_authenticate(user=test_librarian)
            url = '/api/v1/library/books/'
            data = {
                'title': 'Test Book',
                'author': 'Test Author',
                'isbn': '1234567890123',
                'publisher': 'Test Publisher',
                'publication_year': 2024,
                'copies': 5,
                'status': 'available',
                'school': tenant.id
            }
            response = api_client.post(url, data, format='json')
            assert response.status_code == status.HTTP_201_CREATED
            assert Book.objects.count() == 1
            book = Book.objects.first()
            assert book.title == 'Test Book'
            assert book.copies == 5
            assert book.available_copies == 5
            assert book.school_id == tenant.id

    @pytest.mark.django_db(transaction=True)
    def test_issue_book(self, api_client, tenant, test_librarian, test_student):
        # Ensure school is approved in public schema
        with schema_context('public'):
            tenant.is_approved = True
            tenant.save()
            
        with schema_context(tenant.schema_name):
            api_client.force_authenticate(user=test_librarian)
            
            # Create a book first
            school = School.objects.get(id=tenant.id)  # Get school from current schema
            book = Book.objects.create(
                title='Test Book',
                author='Test Author',
                isbn='1234567890123',
                publisher='Test Publisher',
                publication_year=2024,
                copies=5,
                status='available',
                school=school  # Use school from current schema
            )
            
            url = f'/api/v1/library/books/{book.id}/issue/'
            data = {
                'student': test_student.id,
                'issue_date': datetime.now().date().isoformat(),
                'due_date': (datetime.now() + timedelta(days=14)).date().isoformat()
            }
            response = api_client.post(url, data)
            assert response.status_code == status.HTTP_201_CREATED
            assert BookIssue.objects.count() == 1
            book_issue = BookIssue.objects.first()
            assert book_issue.book == book
            assert book_issue.student == test_student

    @pytest.mark.django_db(transaction=True)
    def test_return_book(self, api_client, tenant, test_librarian, test_student):
        # Ensure school is approved in public schema
        with schema_context('public'):
            tenant.is_approved = True
            tenant.save()
            
        with schema_context(tenant.schema_name):
            api_client.force_authenticate(user=test_librarian)
            
            # Create and issue a book
            school = School.objects.get(id=tenant.id)  # Get school from current schema
            book = Book.objects.create(
                title='Test Book',
                author='Test Author',
                isbn='1234567890123',
                publisher='Test Publisher',
                publication_year=2024,
                copies=5,
                status='available',
                school=school  # Use school from current schema
            )
            
            book_issue = BookIssue.objects.create(
                book=book,
                student=test_student,
                issue_date=datetime.now().date(),
                due_date=(datetime.now() + timedelta(days=14)).date()
            )
            
            url = f'/api/v1/library/book-issues/{book_issue.pk}/return/'
            response = api_client.post(url)
            assert response.status_code == status.HTTP_200_OK
            book_issue.refresh_from_db()
            assert book_issue.return_date is not None

    @pytest.mark.django_db(transaction=True)
    def test_book_availability(self, api_client, tenant, test_librarian):
        # Set up test in tenant schema
        with schema_context(tenant.schema_name):
            
            api_client.force_authenticate(user=test_librarian)
            
            # Create book in tenant schema
            # Create book in tenant schema with proper school reference
            # Get school from current schema for test_book_availability
            school = School.objects.get(id=tenant.id)
            book = Book.objects.create(
                title='Test Book',
                author='Test Author',
                isbn='1234567890123',
                publisher='Test Publisher',
                publication_year=2024,
                copies=1,
                available_copies=1,
                status='available',
                school=school  # Use school from current schema
            )
            
            url = f'/api/v1/library/books/{book.pk}/availability/'
            response = api_client.get(url)
            assert response.status_code == status.HTTP_200_OK
            assert response.data['available'] == 1
