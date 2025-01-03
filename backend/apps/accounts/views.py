from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import StudentProfile, TeacherProfile
from .serializers import CustomTokenObtainPairSerializer

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
from .serializers import (
    UserSerializer,
    UserCreateSerializer,
    StudentProfileSerializer,
    TeacherProfileSerializer,
    LoginSerializer,
    ChangePasswordSerializer,
    ProfileUpdateSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
)
from .permissions import IsAdminUser, IsTeacherUser, IsStudentUser

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action in ["create", "login"]:
            return [AllowAny()]
        return super().get_permissions()
        
    def perform_create(self, serializer):
        """Create user within tenant schema context."""
        serializer.save()

    @action(detail=False, methods=["post"])
    def login(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        from django_tenants.utils import schema_context
        with schema_context(request.tenant.schema_name):
            user = User.objects.filter(
                username=serializer.validated_data["username"]
            ).first()
            if user and user.check_password(serializer.validated_data["password"]):
                refresh = RefreshToken.for_user(user)
                return Response(
                    {
                        "access": str(refresh.access_token),
                        "refresh": str(refresh),
                        "user": UserSerializer(user).data,
                    }
                )
            return Response(
                {"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
            )

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def change_password(self, request, pk=None):
        from django_tenants.utils import schema_context
        with schema_context(self.request.tenant.schema_name):
            user = self.get_object()
            serializer = ChangePasswordSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            if not user.check_password(serializer.validated_data["old_password"]):
                return Response(
                    {"detail": "Invalid old password"}, status=status.HTTP_400_BAD_REQUEST
                )

            user.set_password(serializer.validated_data["new_password"])
            user.save()
            return Response({"detail": "Password changed successfully"})

    @action(detail=False, methods=["put"], permission_classes=[IsAuthenticated])
    def update_profile(self, request):
        serializer = ProfileUpdateSerializer(
            request.user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def me(self, request):
        """Get current user data."""
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def reset_password_request(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        user = User.objects.filter(email=email).first()
        if user:
            # TODO: Send password reset email
            pass
        return Response({"detail": "Password reset email sent if account exists"})

    @action(detail=False, methods=["post"])
    def reset_password_confirm(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # TODO: Implement token validation and password reset
        return Response({"detail": "Password reset successful"})


from rest_framework.pagination import PageNumberPagination

class StudentProfilePagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class StudentProfileViewSet(viewsets.ModelViewSet):
    serializer_class = StudentProfileSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StudentProfilePagination

    queryset = StudentProfile.objects.all()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get_queryset(self):
        user = self.request.user
        from django_tenants.utils import schema_context
        with schema_context(self.request.tenant.schema_name):
            if user.role == User.SUPER_ADMIN:
                return StudentProfile.objects.all()
            elif user.role == User.SCHOOL_ADMIN:
                return StudentProfile.objects.filter(user__school=user.school)
            elif user.role == User.TEACHER:
                return StudentProfile.objects.filter(
                    user__school=user.school, section__in=user.sections.all()
                )
            elif user.role == User.STUDENT:
                return StudentProfile.objects.filter(user=user)
            elif user.role == User.PARENT:
                return StudentProfile.objects.filter(parent=user)
            return StudentProfile.objects.none()


class TeacherProfileViewSet(viewsets.ModelViewSet):
    queryset = TeacherProfile.objects.all()
    serializer_class = TeacherProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == User.SUPER_ADMIN:
            return TeacherProfile.objects.all()
        elif user.role == User.SCHOOL_ADMIN:
            return TeacherProfile.objects.filter(user__school=user.school)
        elif user.role == User.TEACHER:
            return TeacherProfile.objects.filter(user=user)
        return TeacherProfile.objects.none()
