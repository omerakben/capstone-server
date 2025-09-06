"""
ViewSets for workspace management in the DEADLINE API.

This module provides RESTful API endpoints for workspace CRUD operations
with Firebase UID-based ownership and proper permission checks.
"""

from artifacts.serializers import ArtifactSerializer
from auth_firebase.permissions import IsOwner
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Workspace
from .serializers import WorkspaceSerializer


class WorkspaceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing workspaces.

    Provides standard CRUD operations for workspaces with automatic
    owner_uid filtering based on authenticated user.
    """

    serializer_class = WorkspaceSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        """
        Filter workspaces by authenticated user's UID.

        Uses prefetch_related to optimize artifact loading and
        avoid N+1 queries when computing artifact counts.
        """
        if hasattr(self.request.user, "uid"):
            return Workspace.objects.filter(
                owner_uid=self.request.user.uid
            ).prefetch_related(  # type: ignore
                "artifacts",
                "workspace_environments__environment_type",
            )
        return Workspace.objects.none()

    def perform_create(self, serializer):
        """Set owner_uid to authenticated user's UID when creating workspace."""
        if hasattr(self.request.user, "uid"):
            serializer.save(owner_uid=self.request.user.uid)  # type: ignore
        else:
            # This should not happen with proper authentication
            raise ValueError("Authentication required")

    @action(detail=True, methods=["get"], url_path="export")
    def export_workspace(self, request, pk=None):  # type: ignore[override]
        """
        Export a workspace with all its artifacts.

        Returns a simple JSON payload the frontend can download.
        """
        workspace = self.get_object()
        ws_data = WorkspaceSerializer(workspace).data
        # Serialize artifacts for this workspace without pagination
        from artifacts.models import Artifact

        artifacts_qs = Artifact.objects.filter(workspace=workspace).order_by("id")
        artifacts_data = ArtifactSerializer(artifacts_qs, many=True).data
        payload = {
            "workspace": ws_data,
            "artifacts": artifacts_data,
            "exportedAt": self._now_iso(),
            "version": "1.0.0",
        }
        return Response(payload)

    @action(detail=False, methods=["post"], url_path="import")
    def import_workspace(self, request):  # type: ignore[override]
        """
        Import a workspace with artifacts from an exported JSON payload.

        Expected payload:
        { workspace: { name, description? }, artifacts: [...], version }
        """
        data = request.data or {}
        ws_in = data.get("workspace") or {}
        artifacts_in = data.get("artifacts") or []

        if not isinstance(ws_in, dict) or not ws_in.get("name"):
            return Response(
                {"error": "Invalid workspace data"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Create workspace for current user; adjust name if exists
        base_name = str(ws_in.get("name")).strip()
        desc = (ws_in.get("description") or "").strip()

        # Enforce owner
        owner_uid = getattr(request.user, "uid", None)
        if not owner_uid:
            return Response(
                {"error": "Authentication required"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        name = base_name
        suffix = 1
        while Workspace.objects.filter(owner_uid=owner_uid, name=name).exists():
            suffix += 1
            # Use hyphenated suffix to satisfy name validation (no parentheses)
            name = f"{base_name} - {suffix}"

        ws = Workspace.objects.create(name=name, description=desc, owner_uid=owner_uid)

        created = []
        for a in artifacts_in:
            if not isinstance(a, dict):
                continue
            payload = dict(a)
            payload.pop("id", None)
            payload.pop("workspace", None)
            # Attach workspace
            serializer = ArtifactSerializer(data=payload)
            if serializer.is_valid():
                serializer.save(workspace=ws)
                created.append(serializer.data)
            # else: silently skip invalid artifacts for MVP import

        out = WorkspaceSerializer(ws).data
        return Response(
            {"workspace": out, "imported_count": len(created)},
            status=status.HTTP_201_CREATED,
        )

    def _now_iso(self):
        from datetime import datetime, timezone

        return datetime.now(timezone.utc).isoformat()
