from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User


def style_form(form):
    for field in form.fields.values():
        widget = field.widget
        if isinstance(widget, forms.CheckboxInput):
            css = "form-check-input"
        elif isinstance(widget, (forms.Select, forms.SelectMultiple)):
            css = "form-select"
        else:
            css = "form-control"
        widget.attrs["class"] = f"{widget.attrs.get('class', '')} {css}".strip()


class DateInput(forms.DateInput):
    input_type = "date"

    def __init__(self, attrs=None, format=None):
        super().__init__(attrs, format or "%Y-%m-%d")


class TimeInput(forms.TimeInput):
    input_type = "time"

    def __init__(self, attrs=None, format=None):
        super().__init__(attrs, format or "%H:%M")


class DateTimeInput(forms.DateTimeInput):
    input_type = "datetime-local"

    def __init__(self, attrs=None, format=None):
        super().__init__(attrs, format or "%Y-%m-%dT%H:%M")


class StyleMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_form(self)


class BModelForm(StyleMixin, forms.ModelForm):
    """Bootstrap-styled ModelForm that knows the current user and can auto-assign an owner field."""

    owner_field = None

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        if self.owner_field and self.user and getattr(self.instance, f"{self.owner_field}_id") is None:
            setattr(self.instance, self.owner_field, self.user)
        return super().save(commit)


class LoginForm(StyleMixin, forms.Form):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={"autofocus": True, "autocomplete": "username"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}))


class MFACodeForm(StyleMixin, forms.Form):
    code = forms.CharField(
        label="6-digit code", min_length=6, max_length=6,
        widget=forms.TextInput(attrs={"autocomplete": "one-time-code", "inputmode": "numeric", "autofocus": True}),
    )


class RegisterForm(StyleMixin, UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email", "role", "student_id", "department")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["role"].choices = [(r, l) for r, l in User.Role.choices if r in ("student", "teacher")]
        self.fields["first_name"].required = True
        self.fields["last_name"].required = True

    def clean_role(self):
        role = self.cleaned_data["role"]
        if role not in ("student", "teacher"):
            raise forms.ValidationError("Invalid role.")
        return role

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_approved = user.role == "student"  # teachers wait for admin approval
        if commit:
            user.save()
        return user


class AdminUserCreateForm(StyleMixin, UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email", "role", "student_id", "department")


class ProfileForm(BModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "phone", "address", "department", "program", "batch", "photo"]


class AdminUserForm(BModelForm):
    unlock = forms.BooleanField(required=False, label="Unlock account / clear failed logins")
    reset_mfa = forms.BooleanField(required=False, label="Reset MFA (user must enrol again)")

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "role", "student_id", "department",
                  "is_active", "is_approved"]

    def clean(self):
        data = super().clean()
        if self.instance.pk and self.user and self.instance.pk == self.user.pk:
            if data.get("role") != "admin" or not data.get("is_active"):
                raise forms.ValidationError("You cannot demote or deactivate your own account.")
        return data

    def save(self, commit=True):
        user = super().save(commit=False)
        if self.cleaned_data.get("unlock"):
            user.failed_attempts = 0
            user.locked_until = None
        if self.cleaned_data.get("reset_mfa"):
            user.mfa_enabled = False
            user.mfa_secret = ""
        if commit:
            user.save()
        return user
