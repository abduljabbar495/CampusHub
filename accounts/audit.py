import ipaddress


def get_ip(request):
    raw = request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip() or request.META.get("REMOTE_ADDR", "")
    try:
        return str(ipaddress.ip_address(raw))
    except ValueError:
        return None


def audit(request, action, detail="", user=None):
    """Write an entry to the audit log."""
    from .models import AuditLog

    actor = user
    if actor is None and getattr(request, "user", None) is not None and request.user.is_authenticated:
        actor = request.user
    username = actor.username if actor else (request.POST.get("username", "") if request.method == "POST" else "")
    AuditLog.objects.create(
        user=actor,
        username=username[:150],
        action=action,
        detail=str(detail)[:1000],
        ip_address=get_ip(request),
    )
