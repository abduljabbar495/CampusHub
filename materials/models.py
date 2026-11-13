from django.conf import settings
from django.db import models
from academics.models import Course

def material_upload_path(instance, filename):
    return f"course_materials/course_{instance.course_id}/{filename}"

class CourseMaterial(models.Model):
    class Category(models.TextChoices):
        NOTES = "NOTES", "Lecture Notes"
        SLIDES = "SLIDES", "Slides"
        BOOKS = "BOOKS", "Books"
        REFERENCES = "REFERENCES", "References"
        OTHER = "OTHER", "Other"
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="materials")
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=12, choices=Category.choices, default=Category.NOTES)
    file = models.FileField(upload_to=material_upload_path)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.title
