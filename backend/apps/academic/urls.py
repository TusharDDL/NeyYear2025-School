from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = "academic"

router = DefaultRouter()
router.register("academic-years", views.AcademicYearViewSet, basename="academic-year")
router.register("classes", views.ClassViewSet, basename="class")
router.register("sections", views.SectionViewSet, basename="section")
router.register("subjects", views.SubjectViewSet, basename="subject")
router.register("attendance", views.AttendanceViewSet, basename="attendance")
router.register("assessments", views.AssessmentViewSet, basename="assessment")
router.register(
    "assessment-results", views.AssessmentResultViewSet, basename="assessment-result"
)
router.register("assignments", views.AssignmentViewSet, basename="assignment")
router.register(
    "assignment-submissions",
    views.AssignmentSubmissionViewSet,
    basename="assignment-submission",
)
router.register("timetable", views.TimetableViewSet, basename="timetable")
router.register("teachers", views.TeacherViewSet, basename="teacher")
router.register("students", views.StudentViewSet, basename="student")

urlpatterns = [
    path("", include(router.urls)),
]
