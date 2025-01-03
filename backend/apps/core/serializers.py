from rest_framework import serializers
from .models import School


class SchoolSerializer(serializers.ModelSerializer):
    schema_name = serializers.CharField(read_only=True)  # From TenantMixin

    class Meta:
        model = School
        fields = [
            "id",
            "schema_name",  # Add this from TenantMixin
            "name",
            "address",
            "contact_email",
            "contact_phone",
            "is_active",
            "board_affiliation",
            "student_strength",
            "staff_count",
            "principal_name",
            "principal_email",
            "principal_phone",
            "is_approved",
            "approval_date",
            "rejection_reason",
            "academic_year_start",
            "academic_year_end",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "schema_name",
            "is_approved",
            "approval_date",
            "rejection_reason",
            "created_at",
            "updated_at",
        ]

    def validate(self, data):
        """
        Validate the student and staff counts against free tier limits
        """
        if data.get("student_strength", 0) > 500:
            raise serializers.ValidationError(
                {"student_strength": "Free tier allows maximum of 500 students"}
            )

        if data.get("staff_count", 0) > 50:
            raise serializers.ValidationError(
                {"staff_count": "Free tier allows maximum of 50 staff members"}
            )

        return data

    def create(self, validated_data):
        """
        Create a new school instance with default values
        """
        validated_data["auto_create_schema"] = True
        return super().create(validated_data)


class SchoolRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = School
        fields = [
            "name",
            "schema_name",  # Add this
            "address",
            "contact_email",
            "contact_phone",
            "board_affiliation",
            "student_strength",
            "staff_count",
            "principal_name",
            "principal_email",
            "principal_phone",
            "academic_year_start",
            "academic_year_end",
        ]

    def validate_schema_name(self, value):
        """Validate schema_name for tenant"""
        if not value.isalnum():
            raise serializers.ValidationError(
                "Schema name must contain only alphanumeric characters"
            )
        return value.lower()

    def create(self, validated_data):
        validated_data["is_active"] = True
        validated_data["auto_create_schema"] = True
        return super().create(validated_data)
