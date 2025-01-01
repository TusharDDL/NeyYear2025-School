from rest_framework import serializers
from .models import Book, BookIssue


class BookSerializer(serializers.ModelSerializer):
    """
    Serializer for Book model.
    """
    class Meta:
        model = Book
        fields = [
            'id', 'title', 'author', 'isbn', 'publisher',
            'publication_year', 'copies', 'available_copies',
            'status', 'school', 'created_at', 'updated_at'
        ]
        read_only_fields = ['available_copies', 'status']


class BookIssueSerializer(serializers.ModelSerializer):
    """
    Serializer for BookIssue model.
    """
    class Meta:
        model = BookIssue
        fields = [
            'id', 'book', 'student', 'school', 'issue_date', 'due_date',
            'return_date', 'status', 'fine_amount', 'remarks',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['return_date', 'fine_amount']
