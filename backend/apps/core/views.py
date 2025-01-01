from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from .models import School
from .serializers import SchoolSerializer
from .permissions import IsSuperAdmin
import logging

logger = logging.getLogger(__name__)

class SchoolViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing schools in the system.
    """
    queryset = School.objects.all()
    serializer_class = SchoolSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'approve']:
            return [IsSuperAdmin()]
        return super().get_permissions()

    @action(detail=True, methods=['post'], url_path='approve', url_name='approve')
    def approve(self, request, pk=None):
        """
        Approve a school registration and create admin credentials.
        """
        school = self.get_object()
        
        if school.is_approved:
            return Response(
                {"detail": "School is already approved."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                school.is_approved = True
                school.approval_date = timezone.now()
                school.save()

                logger.info(f"School approved: {school.name}")
                return Response(
                    {"detail": "School approved successfully."},
                    status=status.HTTP_200_OK
                )

        except Exception as e:
            logger.error(f"Failed to approve school {school.name}: {str(e)}")
            return Response(
                {"detail": "Failed to approve school."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def perform_create(self, serializer):
        """Create a new school."""
        try:
            school = serializer.save()
            logger.info(f"New school created: {school.name}")
        except Exception as e:
            logger.error(f"Failed to create school: {str(e)}")
            raise
