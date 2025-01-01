from rest_framework import serializers
from .models import School

class SchoolSerializer(serializers.ModelSerializer):
    """
    Serializer for the School model.
    """
    class Meta:
        model = School
        fields = ['id', 'name', 'domain_url', 'schema_name', 'admin_email', 
                 'contact_number', 'address', 'is_approved', 'created_at', 'updated_at']
        read_only_fields = ['is_approved', 'created_at', 'updated_at']
