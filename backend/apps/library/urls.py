from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = "library"

router = DefaultRouter()
router.register(r"books", views.BookViewSet, basename="book")
router.register(r"book-issues", views.BookIssueViewSet, basename="book-issue")

urlpatterns = [
    path("", include(router.urls)),
]
