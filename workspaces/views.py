"""
ViewSets for workspace management in the DEADLINE API.

This module provides RESTful API endpoints for workspace CRUD operations
with Firebase UID-based ownership and proper permission checks.
"""

from rest_framework import viewsets

from auth_firebase.permissions import IsOwner

from .models import Workspace
from .serializers import WorkspaceSerializer


class WorkspaceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing workspaces.

    Provides standard CRUD operations for workspaces with automatic
    owner_uid filtering based on authenticated user.
    """

    serializer_class = WorkspaceSerializer
    permission_classes = [IsOwner]

    def get_queryset(self):
        """
        Filter workspaces by authenticated user's UID.

        Uses prefetch_related to optimize artifact loading and
        avoid N+1 queries when computing artifact counts.
        """
        if hasattr(self.request.user, "uid"):
            return Workspace.objects.filter(
                owner_uid=self.request.user.uid  # type: ignore
            ).prefetch_related("artifacts")
        return Workspace.objects.none()

    def perform_create(self, serializer):
        """Set owner_uid to authenticated user's UID when creating workspace."""
        if hasattr(self.request.user, "uid"):
            serializer.save(owner_uid=self.request.user.uid)  # type: ignore
        else:
            # This should not happen with proper authentication
            raise ValueError("Authentication required")
