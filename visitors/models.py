import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone

class Visitor(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        CHECKED_IN = "CHECKED_IN", "Checked-in"
        CHECKED_OUT = "CHECKED_OUT", "Checked-out"
    name = models.CharField(max_length=120)
    phone = models.CharField(max_length=20)
    identity_number = models.CharField(max_length=60, blank=True)
    purpose = models.CharField(max_length=255)
    person_to_visit = models.CharField(max_length=120)
    department = models.CharField(max_length=120, blank=True)
    photo = models.ImageField(upload_to="visitor_photos/", blank=True, null=True)
    pass_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    registered_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="registered_visitors")
    check_in_at = models.DateTimeField(null=True, blank=True)
    check_out_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"{self.name} ({self.pass_id})"
    def check_in(self):
        if self.status != self.Status.PENDING: return False
        self.status = self.Status.CHECKED_IN
        self.check_in_at = timezone.now()
        self.save(update_fields=["status", "check_in_at"])
        return True
    def check_out(self):
        if self.status != self.Status.CHECKED_IN: return False
        self.status = self.Status.CHECKED_OUT
        self.check_out_at = timezone.now()
        self.save(update_fields=["status", "check_out_at"])
        return True
