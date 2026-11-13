from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

class CampusIdentifierBackend(ModelBackend):
    """Authenticate with username, Student ID, or Teacher ID."""
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        identifier = username or kwargs.get("identifier")
        if not identifier or not password:
            return None
        matches = UserModel._default_manager.filter(username__iexact=identifier)
        # IDs are unique by convention; only accept a single matching account.
        id_matches = UserModel._default_manager.filter(student_id__iexact=identifier) | UserModel._default_manager.filter(teacher_id__iexact=identifier)
        candidates = (matches | id_matches).distinct()
        if candidates.count() != 1:
            return None
        user = candidates.first()
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
