from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from .models import Book, BookIssue
from .serializers import BookSerializer, BookIssueSerializer
from django.utils import timezone
from apps.accounts.models import User


class BookViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing books in the library.
    """

    serializer_class = BookSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filter queryset by tenant."""
        from django_tenants.utils import schema_context
        from django.db import connection, transaction
        import logging

        logger = logging.getLogger("apps.library")
        tenant = self.request.tenant
        logger.info(f"Getting books for tenant: {tenant.name}")

        with schema_context(tenant.schema_name):
            connection.set_tenant(tenant)
            with transaction.atomic():
                try:
                    queryset = Book.objects.select_related("school").filter(
                        school=tenant
                    )
                    count = queryset.count()
                    logger.info(f"Found {count} books in schema {tenant.schema_name}")
                    return queryset.all()
                except Exception as e:
                    logger.error(f"Error getting books: {str(e)}", exc_info=True)
                    raise

    def perform_create(self, serializer):
        """Create a book within tenant schema context."""
        if self.request.user.role != "librarian":
            raise PermissionDenied("Only librarians can create books")
        from django_tenants.utils import schema_context
        from django.db import transaction, connection
        import logging

        logger = logging.getLogger("apps.library")
        tenant = self.request.tenant
        logger.info(f"Creating book for tenant: {tenant.name}")

        with schema_context(tenant.schema_name):
            connection.set_tenant(tenant)
            with transaction.atomic():
                try:
                    instance = serializer.save(school=tenant)
                    logger.info(
                        f"Created book {instance.pk} in schema {tenant.schema_name}"
                    )
                    return instance
                except Exception as e:
                    logger.error(f"Error creating book: {str(e)}", exc_info=True)
                    raise

    @action(detail=True, methods=["get"], url_path="availability")
    def check_availability(self, request, pk=None):
        """Check book availability."""
        from django_tenants.utils import schema_context

        with schema_context(self.request.tenant.schema_name):
            book = self.get_object()
            return Response({"available": book.available_copies, "status": book.status})

    @action(detail=True, methods=["post"], url_path="issue")
    def issue_book(self, request, pk=None):
        """Issue a book to a student."""
        if request.user.role != "librarian":
            raise PermissionDenied("Only librarians can issue books")

        from django_tenants.utils import schema_context, get_tenant_model
        from django.db import transaction, connection
        import logging

        logger = logging.getLogger("apps.library")
        tenant = self.request.tenant
        logger.info(f"Issuing book for tenant: {tenant.name}")

        with schema_context(tenant.schema_name):
            connection.set_tenant(tenant)
            with transaction.atomic():
                try:
                    # Get book within tenant context
                    book = Book.objects.get(pk=pk, school=tenant)
                    student_id = request.data.get("student")
                    if not student_id:
                        return Response(
                            {"error": "Student ID is required"},
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                    try:
                        student = User.objects.get(id=student_id, school=tenant)
                    except User.DoesNotExist:
                        return Response(
                            {"error": "Student not found"},
                            status=status.HTTP_404_NOT_FOUND,
                        )

                    if book.available_copies <= 0:
                        return Response(
                            {"error": "No copies available"},
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                    # Create book issue within tenant context
                    book_issue = BookIssue.objects.create(
                        book=book,
                        student=student,
                        school=tenant,
                        issue_date=request.data.get(
                            "issue_date", timezone.now().date()
                        ),
                        due_date=request.data.get(
                            "due_date",
                            timezone.now().date() + timezone.timedelta(days=14),
                        ),
                    )

                    # Update book availability
                    book.available_copies -= 1
                    if book.available_copies == 0:
                        book.status = "issued"
                    book.save()

                    logger.info(
                        f"Book {book.id} issued to student {student.id} in schema {tenant.schema_name}"
                    )
                    return Response(
                        BookIssueSerializer(book_issue).data,
                        status=status.HTTP_201_CREATED,
                    )

                except Book.DoesNotExist:
                    logger.error(f"Book {pk} not found in schema {tenant.schema_name}")
                    return Response(
                        {"error": "Book not found"}, status=status.HTTP_404_NOT_FOUND
                    )
                except Exception as e:
                    logger.error(f"Error issuing book: {str(e)}", exc_info=True)
                    raise


class BookIssueViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing book issues.
    """

    serializer_class = BookIssueSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filter queryset by tenant."""
        if self.request.user.role != "librarian":
            raise PermissionDenied("Only librarians can view book issues")

        from django_tenants.utils import schema_context
        from django.db import connection, transaction
        import logging

        logger = logging.getLogger("apps.library")
        tenant = self.request.tenant
        logger.info(f"Getting book issues for tenant: {tenant.name}")

        with schema_context(tenant.schema_name):
            connection.set_tenant(tenant)
            with transaction.atomic():
                try:
                    queryset = BookIssue.objects.select_related(
                        "book", "student", "school"
                    ).filter(school=tenant)
                    count = queryset.count()
                    logger.info(
                        f"Found {count} book issues in schema {tenant.schema_name}"
                    )
                    return queryset.all()
                except Exception as e:
                    logger.error(f"Error getting book issues: {str(e)}", exc_info=True)
                    raise

    @action(detail=True, methods=["post"], url_path="return")
    def return_book(self, request, pk=None):
        """Return a book."""
        if request.user.role != "librarian":
            raise PermissionDenied("Only librarians can return books")

        from django_tenants.utils import schema_context
        from django.db import transaction, connection
        import logging

        logger = logging.getLogger("apps.library")
        tenant = self.request.tenant
        logger.info(f"Returning book for tenant: {tenant.name}")

        with schema_context(tenant.schema_name):
            connection.set_tenant(tenant)
            with transaction.atomic():
                try:
                    # Get book issue within tenant context
                    book_issue = BookIssue.objects.select_related("book").get(
                        pk=pk, school=tenant
                    )
                    if book_issue.return_date:
                        return Response(
                            {"error": "Book already returned"},
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                    book_issue.return_date = timezone.now().date()
                    book_issue.save()

                    book = book_issue.book
                    book.available_copies += 1
                    if book.available_copies > 0:
                        book.status = "available"
                    book.save()

                    logger.info(
                        f"Book {book.id} returned successfully in schema {tenant.schema_name}"
                    )
                    return Response(
                        {"message": "Book returned successfully"},
                        status=status.HTTP_200_OK,
                    )

                except BookIssue.DoesNotExist:
                    logger.error(
                        f"Book issue {pk} not found in schema {tenant.schema_name}"
                    )
                    return Response(
                        {"error": "Book issue not found"},
                        status=status.HTTP_404_NOT_FOUND,
                    )
                except Exception as e:
                    logger.error(f"Error returning book: {str(e)}", exc_info=True)
                    raise
