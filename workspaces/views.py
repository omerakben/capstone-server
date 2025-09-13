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
            )
        return Workspace.objects.none()

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        # Avoid extra queries in list view by skipping enabled_environments
        # computation; detail views can compute it as needed.
        try:
            if getattr(self, "action", None) == "list":
                ctx["include_enabled_environments"] = False
        except Exception:
            pass
        return ctx

    def perform_create(self, serializer):
        """Create workspace and auto-enable all environment types.

        Sets owner_uid from the authenticated user and creates
        WorkspaceEnvironment rows for all EnvironmentType records so that
        the M2M join is immediately usable by serializers and filters.
        """
        if not hasattr(self.request.user, "uid"):
            # This should not happen with proper authentication
            raise ValueError("Authentication required")

        workspace = serializer.save(owner_uid=self.request.user.uid)  # type: ignore

        # Auto-enable all known environments for the new workspace
        try:
            # Local import to avoid potential circulars at import time
            from .models import EnvironmentType, WorkspaceEnvironment

            env_types = list(EnvironmentType.objects.all())
            if env_types:
                WorkspaceEnvironment.objects.bulk_create(
                    [
                        WorkspaceEnvironment(workspace=workspace, environment_type=et)
                        for et in env_types
                    ],
                    ignore_conflicts=True,
                )
        except Exception:
            # In DEBUG/development we prefer not to fail workspace creation
            # if environment seeding is unavailable; the UI falls back to
            # default envs and artifacts still work via legacy field.
            pass

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

    @action(detail=True, methods=["patch"], url_path="enabled_environments")
    def enabled_environments(self, request, pk=None):  # type: ignore[override]
        """
        Toggle enabled environments (WorkspaceEnvironment joins) for a workspace.

        Payload: { "enabled": ["DEV", "STAGING", "PROD"] }

        Rules:
        - Create joins for any newly enabled slugs.
        - Before removing a join, ensure there are no artifacts in that env.
          If artifacts exist, return 400 with a helpful message.
        """
        workspace = self.get_object()

        enabled_slugs = request.data.get("enabled", [])  # type: ignore
        if not isinstance(enabled_slugs, list) or not all(
            isinstance(x, str) for x in enabled_slugs
        ):
            return Response(
                {"error": "enabled must be an array of strings"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Normalize to uppercase known slugs
        target = {s.upper() for s in enabled_slugs if s}
        allowed = {"DEV", "STAGING", "PROD"}
        if not target.issubset(allowed):
            return Response(
                {"error": f"Unknown slugs provided. Allowed: {sorted(allowed)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from artifacts.models import Artifact

        from .models import EnvironmentType, WorkspaceEnvironment

        # Current joins
        current_wes = (
            WorkspaceEnvironment.objects.select_related("environment_type")
            .filter(workspace=workspace)
            .all()
        )
        current = {
            we.environment_type.slug for we in current_wes if we.environment_type
        }

        to_create = target - current
        to_remove = current - target

        # Block removal if artifacts exist in that environment
        blocking = []
        for slug in sorted(to_remove):
            # Prefer join-based check, fallback to legacy char field
            count = Artifact.objects.filter(
                workspace=workspace,
                workspace_env__environment_type__slug=slug,
            ).count()
            if count == 0:
                count = Artifact.objects.filter(
                    workspace=workspace,
                    environment=slug,
                ).count()
            if count > 0:
                blocking.append({"slug": slug, "artifact_count": count})

        if blocking:
            return Response(
                {
                    "error": "Cannot disable environments that have artifacts",
                    "blocking": blocking,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Ensure EnvironmentType rows exist for requested slugs (lazy seed safety)
        if to_create:
            existing_types = {
                et.slug: et
                for et in EnvironmentType.objects.filter(slug__in=list(to_create))
            }
            missing = to_create - set(existing_types.keys())
            if missing:
                name_map = {
                    "DEV": ("Development", 0),
                    "STAGING": ("Staging", 1),
                    "PROD": ("Production", 2),
                }
                for slug in sorted(missing):
                    nm = name_map.get(slug, (slug.title(), 99))
                    et_obj, _ = EnvironmentType.objects.get_or_create(
                        slug=slug,
                        defaults={
                            "name": nm[0],
                            "display_order": nm[1],
                        },
                    )
                    existing_types[slug] = et_obj
            env_types = existing_types
        # Create missing joins
        if to_create:
            WorkspaceEnvironment.objects.bulk_create(
                [
                    WorkspaceEnvironment(
                        workspace=workspace, environment_type=env_types[slug]
                    )
                    for slug in to_create
                    if slug in env_types
                ],
                ignore_conflicts=True,
            )

        # Remove disabled joins
        if to_remove:
            WorkspaceEnvironment.objects.filter(
                workspace=workspace, environment_type__slug__in=list(to_remove)
            ).delete()

        # Return updated enabled list
        # Reuse serializer helper by fetching fresh object
        from .serializers import WorkspaceSerializer

        ws = type(workspace).objects.get(pk=workspace.pk)
        data = WorkspaceSerializer(ws).data
        return Response({"enabled_environments": data.get("enabled_environments", [])})
