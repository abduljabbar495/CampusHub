from django.urls import path

from . import views as v

app_name = "academics"

urlpatterns = [
    path("courses/", v.CourseList.as_view(), name="course_list"),
    path("courses/new/", v.CourseCreate.as_view(), name="course_create"),
    path("courses/<int:pk>/", v.CourseDetail.as_view(), name="course_detail"),
    path("courses/<int:pk>/edit/", v.CourseUpdate.as_view(), name="course_edit"),
    path("courses/<int:pk>/delete/", v.CourseDelete.as_view(), name="course_delete"),
    path("courses/<int:pk>/enroll/", v.enroll, name="enroll"),
    path("courses/<int:pk>/unenroll/", v.unenroll, name="unenroll"),
    path("students/", v.StudentList.as_view(), name="student_list"),
    path("students/<int:pk>/", v.StudentDetail.as_view(), name="student_detail"),
    path("enrollments/", v.EnrollmentList.as_view(), name="enrollment_list"),
    path("enrollments/new/", v.EnrollmentCreate.as_view(), name="enrollment_create"),
    path("enrollments/<int:pk>/delete/", v.EnrollmentDelete.as_view(), name="enrollment_delete"),
    path("schedule/", v.SessionList.as_view(), name="session_list"),
    path("schedule/new/", v.SessionCreate.as_view(), name="session_create"),
    path("schedule/<int:pk>/edit/", v.SessionUpdate.as_view(), name="session_edit"),
    path("schedule/<int:pk>/delete/", v.SessionDelete.as_view(), name="session_delete"),
    path("schedule/<int:pk>/attendance/", v.session_attendance, name="session_attendance"),
    path("attend/<str:token>/", v.attend, name="attend"),
    path("my-attendance/", v.my_attendance, name="my_attendance"),
    path("results/", v.ResultList.as_view(), name="result_list"),
    path("results/new/", v.ResultCreate.as_view(), name="result_create"),
    path("results/<int:pk>/edit/", v.ResultUpdate.as_view(), name="result_edit"),
    path("results/<int:pk>/delete/", v.ResultDelete.as_view(), name="result_delete"),
]
