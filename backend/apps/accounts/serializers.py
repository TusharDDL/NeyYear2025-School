from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import StudentProfile, TeacherProfile

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data["user_id"] = self.user.id
        data["username"] = self.user.username
        data["email"] = self.user.email
        data["role"] = self.user.role
        data["school_id"] = self.user.school_id if self.user.school else None
        return data


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "role",
            "phone",
            "address",
            "profile_picture",
            "created_at",
        ]
        read_only_fields = ["created_at"]


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "email",
            "username",
            "password",
            "confirm_password",
            "first_name",
            "last_name",
            "role",
            "phone",
            "address",
        ]

    def validate(self, data):
        if data["password"] != data.pop("confirm_password"):
            raise serializers.ValidationError("Passwords do not match")
        return data

    def create(self, validated_data):
        """Create a new user within the tenant context."""
        from django_tenants.utils import schema_context
        from django.db import transaction

        # Get the tenant from the context
        request = self.context.get("request")
        if not request or not hasattr(request, "tenant"):
            raise serializers.ValidationError("Tenant context is required")

        tenant = request.tenant

        # Create user within tenant schema context
        with transaction.atomic():
            with schema_context(tenant.schema_name):
                # Set the school
                validated_data["school"] = tenant
                try:
                    return User.objects.create_user(**validated_data)
                except Exception as e:
                    raise serializers.ValidationError(f"Error creating user: {str(e)}")


class StudentProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    username = serializers.CharField(write_only=True)
    email = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)
    first_name = serializers.CharField(write_only=True)
    last_name = serializers.CharField(write_only=True)
    parent = UserSerializer(read_only=True)
    parent_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = StudentProfile
        fields = [
            "id",
            "user",
            "username",
            "email",
            "password",
            "first_name",
            "last_name",
            "admission_number",
            "date_of_birth",
            "gender",
            "blood_group",
            "address",
            "parent",
            "parent_id",
            "parent_name",
            "parent_phone",
            "parent_email",
            "created_at",
        ]
        read_only_fields = ["created_at"]

    def create(self, validated_data):
        from django_tenants.utils import schema_context

        # Get the tenant from the context
        request = self.context.get("request")
        if not request or not hasattr(request, "tenant"):
            raise serializers.ValidationError("Tenant context is required")

        tenant = request.tenant

        # Extract user data
        user_data = {
            "username": validated_data.pop("username"),
            "email": validated_data.pop("email"),
            "password": validated_data.pop("password"),
            "first_name": validated_data.pop("first_name"),
            "last_name": validated_data.pop("last_name"),
            "role": "student",
            "school": tenant,
        }

        # Create user and profile within tenant schema context
        with schema_context(tenant.schema_name):
            # Create user with school association
            try:
                user = User.objects.create_user(**user_data)
            except Exception as e:
                raise serializers.ValidationError(f"Error creating user: {str(e)}")

            # Create student profile
            try:
                parent_id = validated_data.pop("parent_id", None)
                if parent_id:
                    try:
                        parent = User.objects.get(id=parent_id, school=tenant)
                        validated_data["parent"] = parent
                    except User.DoesNotExist:
                        raise serializers.ValidationError("Parent not found")

                student_profile = StudentProfile.objects.create(
                    user=user, **validated_data
                )
                return student_profile
            except Exception as e:
                # Cleanup user if profile creation fails
                user.delete()
                raise serializers.ValidationError(
                    f"Error creating student profile: {str(e)}"
                )


class TeacherProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = TeacherProfile
        fields = [
            "id",
            "user",
            "employee_id",
            "date_of_birth",
            "qualification",
            "experience_years",
            "subjects",
            "created_at",
        ]
        read_only_fields = ["created_at"]


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        if data["new_password"] != data["confirm_password"]:
            raise serializers.ValidationError("New passwords do not match")
        return data


class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "phone", "address", "profile_picture"]


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField()
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        if data["password"] != data["confirm_password"]:
            raise serializers.ValidationError("Passwords do not match")
        return data
