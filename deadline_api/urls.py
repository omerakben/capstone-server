"""
URL configuration for deadline_api project.

DEADLINE - Developer Command Center
API endpoints for managing workspaces, artifacts, and authentication.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    # API endpoints (temporarily commented out until views are created)
    # path("api/v1/workspaces/", include("workspaces.urls")),
    # path("api/v1/artifacts/", include("artifacts.urls")),
    # path("api/v1/auth/", include("auth_firebase.urls")),
    # API documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]

# Debug toolbar for local development
if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
        path("__debug__/", include(debug_toolbar.urls)),
    ] + urlpatterns
