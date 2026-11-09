from functools import wraps

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied

from .audit import audit


def _deny(request):
    audit(request, "ACCESS_DENIED", request.get_full_path())
    raise PermissionDenied


class RoleRequiredMixin(LoginRequiredMixin):
    """Role-Based Access Control for class-based views. allowed_roles=None -> any signed-in user."""

    allowed_roles = None

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if self.allowed_roles and request.user.role not in self.allowed_roles:
            _deny(request)
        return super().dispatch(request, *args, **kwargs)


def role_required(*roles):
    """RBAC decorator for function-based views."""

    def decorator(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            if request.user.role not in roles:
                _deny(request)
            return view(request, *args, **kwargs)

        return login_required(wrapper)

    return decorator
