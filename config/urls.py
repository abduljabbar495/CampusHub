from django.conf import settings
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.urls import include, path, re_path
from django.views.static import serve

urlpatterns = [
    path("manage-admin/", admin.site.urls),
    path("", include("accounts.urls")),
    path("academics/", include("academics.urls")),
    path("campus/", include("campus.urls")),
    path("security/", include("security.urls")),
    # Uploaded files are only served to authenticated users (file names are random UUIDs)
    re_path(r"^media/(?P<path>.*)$", login_required(serve), {"document_root": settings.MEDIA_ROOT}),
]

handler403 = "accounts.views.error_403"
