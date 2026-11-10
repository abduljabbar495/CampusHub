from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import AuditLog, Notification, User


@admin.register(User)
class CampusUserAdmin(UserAdmin):
    list_display = ("username", "email", "role", "is_active", "is_approved", "mfa_enabled")
    list_filter = ("role", "is_active", "is_approved", "mfa_enabled")
    fieldsets = UserAdmin.fieldsets + (
        ("CampusHub", {"fields": ("role", "student_id", "phone", "department", "program", "batch", "address", "photo", "is_approved", "failed_attempts", "locked_until")}),
    )


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("created", "username", "action", "ip_address")
    list_filter = ("action",)
    search_fields = ("username", "detail")

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False


admin.site.register(Notification)
