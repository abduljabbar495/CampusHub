from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("login/", views.login_view, name="login"),
    path("login/mfa/", views.mfa_verify, name="mfa_verify"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register, name="register"),
    path("profile/", views.profile, name="profile"),
    path("profile/edit/", views.ProfileEdit.as_view(), name="profile_edit"),
    path("profile/password/", views.PasswordChange.as_view(), name="password_change"),
    path("profile/mfa/", views.mfa_setup, name="mfa_setup"),
    path("profile/mfa/disable/", views.mfa_disable, name="mfa_disable"),
    path("notifications/", views.notifications, name="notifications"),
    path("users/", views.UserList.as_view(), name="user_list"),
    path("users/create/", views.UserCreate.as_view(), name="user_create"),
    path("users/<int:pk>/edit/", views.UserEdit.as_view(), name="user_edit"),
    path("audit/", views.AuditList.as_view(), name="audit_list"),
    path("audit/export/", views.export, {"kind": "audit"}, name="export_audit"),
    path("reports/", views.reports, name="reports"),
    path("reports/export/<str:kind>/", views.export, name="export"),
]
