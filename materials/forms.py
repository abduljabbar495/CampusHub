from django import forms
from .models import CourseMaterial
ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx", ".ppt", ".pptx", ".jpg", ".jpeg", ".png", ".txt"}
class MaterialForm(forms.ModelForm):
    class Meta:
        model = CourseMaterial
        fields = ("course", "title", "description", "category", "file")
    def clean_file(self):
        f = self.cleaned_data["file"]
        import os
        ext = os.path.splitext(f.name)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise forms.ValidationError("Unsupported file type.")
        if f.size > 10 * 1024 * 1024:
            raise forms.ValidationError("Maximum file size is 10 MB.")
        return f
