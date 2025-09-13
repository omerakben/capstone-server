"""
URLs for artifacts app.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"tags", views.TagViewSet, basename="tag")
router.register(r"", views.ArtifactViewSet, basename="artifact")

urlpatterns = [
    path("", include(router.urls)),
]
