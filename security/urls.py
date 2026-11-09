from django.urls import path

from . import views as v

app_name = "security"

urlpatterns = [
    path("passes/", v.PassList.as_view(), name="pass_list"),
    path("passes/new/", v.pass_create, name="pass_create"),
    path("passes/lookup/", v.pass_lookup, name="pass_lookup"),
    path("passes/<int:pk>/", v.pass_detail, name="pass_detail"),
    path("passes/<int:pk>/action/", v.pass_action, name="pass_action"),
    path("passes/scan/<str:token>/", v.pass_scan, name="pass_scan"),
    path("incidents/", v.IncidentList.as_view(), name="incident_list"),
    path("incidents/new/", v.IncidentCreate.as_view(), name="incident_create"),
    path("incidents/<int:pk>/", v.incident_detail, name="incident_detail"),
]
