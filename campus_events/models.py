from django.conf import settings
from django.db import models

class Notice(models.Model):
    class Category(models.TextChoices):
        ACADEMIC = "ACADEMIC", "Academic"
        EXAM = "EXAM", "Examination"
        HOLIDAY = "HOLIDAY", "Holiday"
        GENERAL = "GENERAL", "General"
    title = models.CharField(max_length=180)
    description = models.TextField()
    category = models.CharField(max_length=12, choices=Category.choices, default=Category.GENERAL)
    attachment = models.FileField(upload_to="notices/", blank=True, null=True)
    priority = models.BooleanField(default=False)
    published = models.BooleanField(default=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.title

class Event(models.Model):
    name = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    event_date = models.DateField()
    start_time = models.TimeField()
    location = models.CharField(max_length=180)
    published = models.BooleanField(default=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ["event_date", "start_time"]
    def __str__(self): return self.name
