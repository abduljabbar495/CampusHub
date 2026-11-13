from django.contrib.auth.decorators import user_passes_test
from functools import wraps

def role_required(*roles):
    def decorator(view_func):
        def check(user):
            return user.is_authenticated and (user.is_superuser or user.role in roles)
        return user_passes_test(check, login_url="login")(view_func)
    return decorator
