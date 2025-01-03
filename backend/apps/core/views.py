from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from .models import School
from .serializers import SchoolSerializer, SchoolRegistrationSerializer
from .permissions import IsSuperAdmin
import logging


logger = logging.getLogger(__name__)


class SchoolViewSet(viewsets.ModelViewSet):
    queryset = School.objects.all()
    serializer_class = SchoolSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "create":
            return SchoolRegistrationSerializer
        return SchoolSerializer

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy", "approve"]:
            return [IsSuperAdmin()]
        return super().get_permissions()

    @action(detail=True, methods=["post"], url_path="approve", url_name="approve")
    def approve(self, request, pk=None):
        school = self.get_object()

        if school.is_approved:
            return Response(
                {"detail": "School is already approved."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with transaction.atomic():
                school.is_approved = True
                school.approval_date = timezone.now()
                school.save()

                # Create domain for the school
                Domain.objects.create(
                    domain=f"{school.schema_name}.{settings.DOMAIN}",
                    tenant=school,
                    is_primary=True,
                )

                logger.info(f"School approved: {school.name}")
                return Response(
                    {"detail": "School approved successfully."},
                    status=status.HTTP_200_OK,
                )

        except Exception as e:
            logger.error(f"Failed to approve school {school.name}: {str(e)}")
            return Response(
                {"detail": "Failed to approve school."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
