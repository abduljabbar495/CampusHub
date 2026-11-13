from django.urls import path
from . import views
urlpatterns = [
    path("notices/", views.notice_list, name="notice_list"),
    path("notices/new/", views.notice_create, name="notice_create"),
    path("notices/<int:pk>/delete/", views.notice_delete, name="notice_delete"),
    path("events/", views.event_list, name="event_list"),
    path("events/new/", views.event_create, name="event_create"),
]
