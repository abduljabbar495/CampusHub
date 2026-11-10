import os
import uuid

from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible

ALLOWED_EXTENSIONS = {
    ".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx",
    ".txt", ".png", ".jpg", ".jpeg", ".zip",
}
MAX_UPLOAD_MB = 10


def validate_upload(f):
    """Secure upload check: extension whitelist + size limit."""
    ext = os.path.splitext(f.name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(f"File type '{ext}' is not allowed.")
    if f.size > MAX_UPLOAD_MB * 1024 * 1024:
        raise ValidationError(f"File too large (max {MAX_UPLOAD_MB} MB).")


@deconstructible
class UploadTo:
    """Stores uploads under a random UUID name so original names are never trusted."""

    def __init__(self, folder):
        self.folder = folder

    def __call__(self, instance, filename):
        ext = os.path.splitext(filename)[1].lower()
        return f"{self.folder}/{uuid.uuid4().hex}{ext}"
