def notify(users, message, url=""):
    """Create in-app notifications for one user or an iterable of users."""
    from .models import Notification

    if hasattr(users, "pk"):
        users = [users]
    Notification.objects.bulk_create(
        [Notification(user=u, message=message[:255], url=url) for u in users]
    )
