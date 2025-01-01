from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

app_name = 'accounts'

router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'students', views.StudentProfileViewSet, basename='student')
router.register(r'teachers', views.TeacherProfileViewSet, basename='teacher')

urlpatterns = [
    path('', include(router.urls)),
    path('token/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('login/', views.UserViewSet.as_view({'post': 'login'}), name='login'),
    path('register/', views.UserViewSet.as_view({'post': 'create'}), name='register'),
    path('users/<int:pk>/change-password/', views.UserViewSet.as_view({'post': 'change_password'}), name='change-password'),
]
