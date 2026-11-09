import secrets
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from accounts.crypto import decrypt, encrypt
from accounts.validators import UploadTo, validate_upload

User = settings.AUTH_USER_MODEL


def new_pass_token():
    return secrets.token_urlsafe(24)


class Visitor(models.Model):
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20)
    id_number_enc = models.CharField(max_length=255, blank=True)  # encrypted at rest
    purpose = models.CharField(max_length=200)
    host_name = models.CharField(max_length=150, help_text="Person / office being visited")
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return self.name

    def set_id_number(self, value):
        self.id_number_enc = encrypt(value)

    def id_masked(self):
        value = decrypt(self.id_number_enc)
        return ("•" * max(len(value) - 3, 0)) + value[-3:] if value else ""


class VisitorPass(models.Model):
    class Status(models.TextChoices):
        ISSUED = "issued", "Issued"
        CHECKED_IN = "checked_in", "Checked in"
        CHECKED_OUT = "checked_out", "Checked out"
        EXPIRED = "expired", "Expired"
        REVOKED = "revoked", "Revoked"

    visitor = models.ForeignKey(Visitor, on_delete=models.CASCADE, related_name="passes")
    token = models.CharField(max_length=64, unique=True, default=new_pass_token)
    valid_from = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField()
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.ISSUED)
    issued_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name="passes_issued")
    checked_in_at = models.DateTimeField(null=True, blank=True)
    checked_out_at = models.DateTimeField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return f"Pass #{self.pk} – {self.visitor}"

    def refresh_status(self):
        """Mark an unused pass as expired once its validity window is over."""
        if self.status == self.Status.ISSUED and timezone.now() > self.valid_until:
            self.status = self.Status.EXPIRED
            self.save(update_fields=["status"])
        return self.status

    def is_valid_now(self):
        return self.valid_from <= timezone.now() <= self.valid_until


class Incident(models.Model):
    class Severity(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        CRITICAL = "critical", "Critical"

    class Status(models.TextChoices):
        REPORTED = "reported", "Reported"
        INVESTIGATING = "investigating", "Investigating"
        RESOLVED = "resolved", "Resolved"
        CLOSED = "closed", "Closed"

    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name="incidents_reported")
    title = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=150)
    occurred_at = models.DateTimeField(default=timezone.now)
    severity = models.CharField(max_length=10, choices=Severity.choices, default=Severity.LOW)
    status = models.CharField(max_length=14, choices=Status.choices, default=Status.REPORTED)
    attachment = models.FileField(upload_to=UploadTo("incidents"), validators=[validate_upload], blank=True)
    assigned_to = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="incidents_assigned")
    resolution_notes = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return self.title
