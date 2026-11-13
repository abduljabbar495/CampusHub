from django import forms
from .models import Visitor
class VisitorForm(forms.ModelForm):
    class Meta:
        model = Visitor
        fields = ("name", "phone", "identity_number", "purpose", "person_to_visit", "department", "photo")
