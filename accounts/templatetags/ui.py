from django import template

register = template.Library()

BADGES = {
    "open": "warning", "in_review": "info", "resolved": "success", "rejected": "danger",
    "reported": "warning", "investigating": "info", "closed": "secondary",
    "low": "success", "medium": "warning", "high": "danger", "critical": "dark",
    "issued": "primary", "checked_in": "success", "checked_out": "secondary",
    "expired": "secondary", "revoked": "danger",
    "student": "primary", "teacher": "info", "staff": "warning", "guard": "dark",
    "admin": "danger", "management": "success",
}


def _resolve(obj, path, display):
    parts = path.split(".")
    for i, part in enumerate(parts):
        if obj is None:
            return ""
        last = i == len(parts) - 1
        if display and last and hasattr(obj, f"get_{part}_display"):
            obj = getattr(obj, f"get_{part}_display")
        else:
            obj = getattr(obj, part, "")
        if callable(obj):
            obj = obj()
    return "" if obj is None else obj


@register.filter
def getvalue(obj, path):
    return _resolve(obj, path, True)


@register.filter
def getraw(obj, path):
    return _resolve(obj, path, False)


@register.filter
def badgecolor(value):
    return BADGES.get(str(value), "secondary")
