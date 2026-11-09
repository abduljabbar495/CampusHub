from django.urls import path

from . import views as v

app_name = "campus"

urlpatterns = [
    path("materials/", v.MaterialList.as_view(), name="material_list"),
    path("materials/new/", v.MaterialCreate.as_view(), name="material_create"),
    path("materials/<int:pk>/delete/", v.MaterialDelete.as_view(), name="material_delete"),
    path("assignments/", v.AssignmentList.as_view(), name="assignment_list"),
    path("assignments/new/", v.AssignmentCreate.as_view(), name="assignment_create"),
    path("assignments/<int:pk>/", v.assignment_detail, name="assignment_detail"),
    path("assignments/<int:pk>/edit/", v.AssignmentUpdate.as_view(), name="assignment_edit"),
    path("assignments/<int:pk>/delete/", v.AssignmentDelete.as_view(), name="assignment_delete"),
    path("submissions/<int:pk>/grade/", v.GradeSubmission.as_view(), name="grade_submission"),
    path("quizzes/", v.QuizList.as_view(), name="quiz_list"),
    path("quizzes/new/", v.QuizCreate.as_view(), name="quiz_create"),
    path("quizzes/<int:pk>/", v.quiz_detail, name="quiz_detail"),
    path("quizzes/<int:pk>/edit/", v.QuizUpdate.as_view(), name="quiz_edit"),
    path("quizzes/<int:pk>/delete/", v.QuizDelete.as_view(), name="quiz_delete"),
    path("quizzes/<int:pk>/take/", v.quiz_take, name="quiz_take"),
    path("quizzes/<int:quiz_pk>/questions/new/", v.QuestionCreate.as_view(), name="question_create"),
    path("questions/<int:pk>/edit/", v.QuestionUpdate.as_view(), name="question_edit"),
    path("questions/<int:pk>/delete/", v.QuestionDelete.as_view(), name="question_delete"),
    path("notices/", v.NoticeList.as_view(), name="notice_list"),
    path("notices/new/", v.NoticeCreate.as_view(), name="notice_create"),
    path("notices/<int:pk>/edit/", v.NoticeUpdate.as_view(), name="notice_edit"),
    path("notices/<int:pk>/delete/", v.NoticeDelete.as_view(), name="notice_delete"),
    path("events/", v.EventList.as_view(), name="event_list"),
    path("events/new/", v.EventCreate.as_view(), name="event_create"),
    path("events/<int:pk>/", v.event_detail, name="event_detail"),
    path("events/<int:pk>/edit/", v.EventUpdate.as_view(), name="event_edit"),
    path("events/<int:pk>/delete/", v.EventDelete.as_view(), name="event_delete"),
    path("complaints/", v.ComplaintList.as_view(), name="complaint_list"),
    path("complaints/new/", v.ComplaintCreate.as_view(), name="complaint_create"),
    path("complaints/<int:pk>/", v.complaint_detail, name="complaint_detail"),
]
