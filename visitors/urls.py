from django.urls import path
from . import views
urlpatterns = [
    path("", views.visitor_list, name="visitor_list"),
    path("register/", views.visitor_register, name="visitor_register"),
    path("<int:pk>/pass/", views.visitor_pass, name="visitor_pass"),
    path("<int:pk>/qr.png", views.visitor_qr, name="visitor_qr"),
    path("scan/<uuid:pass_id>/", views.visitor_scan, name="visitor_scan"),
]
