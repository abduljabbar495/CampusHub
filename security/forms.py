from django import forms

from accounts.forms import BModelForm, DateTimeInput, StyleMixin
from accounts.models import User

from .models import Incident


class VisitorPassForm(StyleMixin, forms.Form):
    name = forms.CharField(max_length=150, label="Visitor name")
    phone = forms.CharField(max_length=20)
    id_number = forms.CharField(max_length=40, label="ID / NID / passport number")
    purpose = forms.CharField(max_length=200)
    host_name = forms.CharField(max_length=150, label="Visiting (person / office)")
    valid_hours = forms.TypedChoiceField(
        label="Pass valid for", coerce=int, initial=4,
        choices=[(h, f"{h} hour{'s' if h > 1 else ''}") for h in (1, 2, 3, 4, 6, 8, 12)],
    )

    def clean_phone(self):
        phone = self.cleaned_data["phone"].strip()
        digits = phone.replace("+", "").replace("-", "").replace(" ", "")
        if not digits.isdigit() or not 7 <= len(digits) <= 15:
            raise forms.ValidationError("Enter a valid phone number.")
        return phone


class PassLookupForm(StyleMixin, forms.Form):
    code = forms.CharField(label="Pass code or scanned link", max_length=300)


class IncidentForm(BModelForm):
    owner_field = "reporter"

    class Meta:
        model = Incident
        fields = ["title", "description", "location", "occurred_at", "severity", "attachment"]
        widgets = {"occurred_at": DateTimeInput(), "description": forms.Textarea(attrs={"rows": 5})}


class IncidentManageForm(BModelForm):
    class Meta:
        model = Incident
        fields = ["severity", "status", "assigned_to", "resolution_notes"]
        widgets = {"resolution_notes": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["assigned_to"].queryset = User.objects.filter(role__in=["guard", "admin"], is_active=True)
