from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SchoolViewSet

app_name = "core"

router = DefaultRouter()
router.register("schools", SchoolViewSet, basename="school")

urlpatterns = [
    path("", include(router.urls)),
]
