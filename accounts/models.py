from datetime import timedelta

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

from .crypto import decrypt, encrypt
from .validators import UploadTo

MAX_FAILED_ATTEMPTS = 5
LOCK_MINUTES = 15


class User(AbstractUser):
    class Role(models.TextChoices):
        STUDENT = "student", "Student"
        TEACHER = "teacher", "Teacher"
        STAFF = "staff", "Administrative Staff"
        GUARD = "guard", "Security Guard"
        ADMIN = "admin", "System Administrator"
        MANAGEMENT = "management", "University Management"

    role = models.CharField(max_length=12, choices=Role.choices, default=Role.STUDENT)
    phone = models.CharField(max_length=20, blank=True)
    department = models.CharField(max_length=100, blank=True)
    student_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    program = models.CharField(max_length=100, blank=True)
    batch = models.CharField(max_length=30, blank=True)
    address = models.CharField(max_length=255, blank=True)
    photo = models.ImageField(upload_to=UploadTo("photos"), blank=True)
    is_approved = models.BooleanField(default=True, help_text="Teachers must be approved by an administrator.")

    # MFA (TOTP). The secret is stored encrypted.
    mfa_enabled = models.BooleanField(default=False)
    mfa_secret = models.CharField(max_length=255, blank=True)

    # Brute-force protection
    failed_attempts = models.PositiveSmallIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["username"]

    def __str__(self):
        return self.get_full_name() or self.username

    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.role = self.Role.ADMIN
        if self.role == self.Role.ADMIN:
            self.is_staff = True
        super().save(*args, **kwargs)

    # --- lockout ---
    def is_locked(self):
        return bool(self.locked_until and self.locked_until > timezone.now())

    def lock(self):
        self.locked_until = timezone.now() + timedelta(minutes=LOCK_MINUTES)
        self.failed_attempts = 0
        self.save(update_fields=["locked_until", "failed_attempts"])

    def register_failure(self):
        self.failed_attempts += 1
        if self.failed_attempts >= MAX_FAILED_ATTEMPTS:
            self.lock()
        else:
            self.save(update_fields=["failed_attempts"])

    def reset_failures(self):
        if self.failed_attempts or self.locked_until:
            self.failed_attempts = 0
            self.locked_until = None
            self.save(update_fields=["failed_attempts", "locked_until"])

    # --- MFA ---
    def set_mfa_secret(self, secret):
        self.mfa_secret = encrypt(secret)

    def get_mfa_secret(self):
        return decrypt(self.mfa_secret)


class AuditLog(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="audit_entries")
    username = models.CharField(max_length=150, blank=True)
    action = models.CharField(max_length=40, db_index=True)
    detail = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return f"{self.created:%Y-%m-%d %H:%M} {self.username} {self.action}"


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    message = models.CharField(max_length=255)
    url = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return self.message
