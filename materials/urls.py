from django.urls import path
from . import views
urlpatterns = [
    path("", views.material_list, name="material_list"),
    path("upload/", views.material_upload, name="material_upload"),
    path("<int:pk>/download/", views.material_download, name="material_download"),
    path("<int:pk>/delete/", views.material_delete, name="material_delete"),
]
