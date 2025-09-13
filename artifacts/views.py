"""
ViewSets for artifact management in the DEADLINE API.

This module provides RESTful API endpoints for artifact CRUD operations
with workspace-based nested routing, Firebase UID-based ownership,
and polymorphic artifact type support.
"""

from auth_firebase.permissions import IsOwner
from django.db import IntegrityError
from django.db.models import Count
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from workspaces.models import Workspace

from .models import Artifact, Tag
from .serializers import ArtifactSerializer, TagSerializer


class ArtifactViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing artifacts within workspaces.

    Provides nested CRUD operations for artifacts under workspaces with:
    - Firebase UID-based ownership through workspace relationship
    - Filtering by artifact kind and environment
    - Search across artifact content
    - Type-specific validation
    - Bulk operations for artifact management
    """

    serializer_class = ArtifactSerializer
    permission_classes = [IsAuthenticated, IsOwner]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["key", "title", "content", "notes", "url", "tags__name"]
    ordering_fields = ["created_at", "updated_at", "kind", "environment"]
    ordering = ["-updated_at"]

    def get_serializer(self, *args, **kwargs):
        """Ensure tag field queryset is workspace-scoped for write operations."""
        serializer = super().get_serializer(*args, **kwargs)
        try:
            ws = self.get_workspace()
            if ws and hasattr(serializer, "fields"):
                if "tags" in serializer.fields:
                    field = serializer.fields["tags"]
                    target = getattr(field, "child_relation", field)
                    target.queryset = Tag.objects.filter(workspace=ws)
        except Exception:
            # Non-fatal safeguard; default behavior still applies
            pass
        return serializer

    def get_queryset(self):
        """
        Filter artifacts by workspace ownership and workspace_id from URL.

        Uses select_related to optimize workspace loading and avoid N+1 queries.
        Only returns artifacts from workspaces owned by authenticated user.
        """
        workspace_id = self.kwargs.get("workspace_id")

        if not workspace_id:
            return Artifact.objects.none()

        # Verify workspace ownership and get artifacts
        if hasattr(self.request.user, "uid"):
            try:
                workspace = get_object_or_404(
                    Workspace.objects.filter(owner_uid=self.request.user.uid),  # type: ignore
                    id=workspace_id,
                )
                return Artifact.objects.filter(workspace=workspace).select_related(
                    "workspace",
                    "workspace_env",
                    "workspace_env__environment_type",
                )
            except (Workspace.DoesNotExist, AttributeError):
                return Artifact.objects.none()

        return Artifact.objects.none()

    def get_workspace(self):
        """Get the workspace for this artifact operation."""
        workspace_id = self.kwargs.get("workspace_id")

        if not workspace_id:
            return None

        if hasattr(self.request.user, "uid"):
            return get_object_or_404(
                Workspace.objects.filter(owner_uid=self.request.user.uid),  # type: ignore
                id=workspace_id,
            )
        return None

    def perform_create(self, serializer):
        """Set workspace from URL when creating artifact."""
        workspace = self.get_workspace()
        if workspace:
            serializer.save(workspace=workspace)
        else:
            raise ValueError("Workspace not found or access denied")

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        workspace = self.get_workspace()
        if workspace:
            ctx["workspace"] = workspace
        return ctx

    def get_queryset_filters(self):
        """Apply query parameter filters manually."""
        queryset = self.get_queryset()

        # Filter by kind
        kind = self.request.query_params.get("kind")  # type: ignore
        if kind:
            queryset = queryset.filter(kind=kind)

        # Filter by environment: support both legacy field and new join
        environment = self.request.query_params.get("environment")  # type: ignore
        if environment:
            try:
                # Prefer join against workspace_env -> environment_type.slug
                queryset = queryset.filter(
                    workspace_env__environment_type__slug=environment
                )
            except Exception:
                # Fallback to legacy char field
                queryset = queryset.filter(environment=environment)

        return queryset

    def list(self, request, *args, **kwargs):
        """Override list to apply custom filtering."""
        queryset = self.get_queryset_filters()

        # Apply search filter
        search_term = request.query_params.get("search")  # type: ignore
        if search_term:
            from django.db.models import Q

            queryset = queryset.filter(
                Q(key__icontains=search_term)
                | Q(title__icontains=search_term)
                | Q(content__icontains=search_term)
                | Q(notes__icontains=search_term)
                | Q(url__icontains=search_term)
            )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="reveal_value")
    def reveal_value(self, request, *args, **kwargs):
        """
        Reveal the unmasked value for an ENV_VAR artifact.

        Security:
        - Uses standard IsAuthenticated + IsOwner checks from the ViewSet.
        - Only permitted for artifacts of kind ENV_VAR.
        - Returns minimal fields necessary for display/copy.
        """
        artifact = self.get_object()
        if artifact.kind != "ENV_VAR":
            return Response(
                {"error": "Not an environment variable"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "id": artifact.id,
                "workspace": artifact.workspace_id,
                "key": artifact.key,
                "value": artifact.value,
                "environment": artifact.environment,
                "updated_at": artifact.updated_at,
            }
        )

    @action(detail=True, methods=["post"])
    def duplicate_to_environment(self, request, *args, **kwargs):
        """
        Duplicate artifact to a different environment by creating a new record
        with the same fields but a different environment slug.
        """
        artifact = self.get_object()
        target_environment = request.data.get("environment")

        if not target_environment:
            return Response(
                {"error": "Target environment is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if target_environment not in ["DEV", "STAGING", "PROD"]:
            return Response(
                {"error": "Invalid environment. Must be DEV, STAGING, or PROD"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if artifact already exists in target environment
        existing_check = {}
        if artifact.kind == "ENV_VAR":
            existing_check = {
                "workspace": artifact.workspace,
                "kind": "ENV_VAR",
                "key": artifact.key,
                "environment": target_environment,
            }
        elif artifact.kind in ["PROMPT", "DOC_LINK"]:
            existing_check = {
                "workspace": artifact.workspace,
                "kind": artifact.kind,
                "title": artifact.title,
                "environment": target_environment,
            }

        if existing_check and Artifact.objects.filter(**existing_check).exists():
            field_name = "key" if artifact.kind == "ENV_VAR" else "title"
            field_value = artifact.key if artifact.kind == "ENV_VAR" else artifact.title
            return Response(
                {
                    "error": f"An artifact with {field_name} '{field_value}' already exists in {target_environment} environment"
                },
                status=status.HTTP_409_CONFLICT,
            )

        duplicate_data = {
            "workspace": artifact.workspace.id,
            "kind": artifact.kind,
            "environment": target_environment,
            "notes": artifact.notes,
            "metadata": artifact.metadata,
        }

        if artifact.kind == "ENV_VAR":
            duplicate_data.update({"key": artifact.key, "value": artifact.value})
        elif artifact.kind == "PROMPT":
            duplicate_data.update(
                {"title": artifact.title, "content": artifact.content}
            )
        elif artifact.kind == "DOC_LINK":
            duplicate_data.update({"title": artifact.title, "url": artifact.url})

        serializer = self.get_serializer(data=duplicate_data)
        if serializer.is_valid():
            serializer.save(workspace=artifact.workspace)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"])
    def bulk_create(self, request, *args, **kwargs):
        """
        Create multiple artifacts in bulk.

        Accepts an array of artifact data and creates them all within
        the workspace, with proper validation for each.
        """
        if not isinstance(request.data, list):
            return Response(
                {"error": "Expected an array of artifact data"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        workspace = self.get_workspace()
        if not workspace:
            return Response(
                {"error": "Workspace not found or access denied"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        created_artifacts = []
        errors = []

        for i, artifact_data in enumerate(request.data):
            # Add workspace to each artifact
            artifact_data["workspace"] = workspace.id

            serializer = self.get_serializer(data=artifact_data)
            if serializer.is_valid():
                serializer.save()
                created_artifacts.append(serializer.data)
            else:
                errors.append(
                    {"index": i, "data": artifact_data, "errors": serializer.errors}
                )

        response_data = {
            "created": created_artifacts,
            "created_count": len(created_artifacts),
            "error_count": len(errors),
        }

        if errors:
            response_data["errors"] = errors

        status_code = (
            status.HTTP_201_CREATED
            if created_artifacts
            else status.HTTP_400_BAD_REQUEST
        )
        return Response(response_data, status=status_code)


class TagViewSet(viewsets.ModelViewSet):
    """Manage tags within a workspace (Many-to-Many for artifacts)."""

    serializer_class = TagSerializer
    permission_classes = [IsAuthenticated, IsOwner]
    # Return a simple array for tags (client expects a list, not paginated)
    pagination_class = None
    queryset = Tag.objects.none()

    def get_workspace(self):
        workspace_id = self.kwargs.get("workspace_id")
        if not workspace_id:
            return None
        if hasattr(self.request.user, "uid"):
            return get_object_or_404(
                Workspace.objects.filter(owner_uid=self.request.user.uid),
                id=workspace_id,
            )
        return None

    def get_queryset(self):
        ws = self.get_workspace()
        if not ws:
            return Tag.objects.none()
        return (
            Tag.objects.filter(workspace=ws)
            .annotate(usage_count=Count("artifact_tags"))
            .order_by("name")
        )

    def get_serializer_context(self):
        """Provide workspace to serializer for validation (e.g., unique name)."""
        ctx = super().get_serializer_context()
        ws = self.get_workspace()
        if ws:
            ctx["workspace"] = ws
        return ctx

    def perform_create(self, serializer):
        ws = self.get_workspace()
        if not ws:
            raise ValueError("Workspace not found or access denied")
        try:
            serializer.save(workspace=ws)
        except IntegrityError:
            # Race condition fallback: ensure clean 400 instead of 500
            raise ValidationError(
                {"name": "A tag with this name already exists in this workspace"}
            )

    @action(detail=False, methods=["delete"])
    def bulk_delete(self, request, *args, **kwargs):
        """
        Delete multiple tags by IDs within the current workspace.

        Body: { "ids": number[] }
        """
        tag_ids = request.data.get("ids", [])

        if not isinstance(tag_ids, list) or not tag_ids:
            return Response(
                {"error": "Expected an array of tag IDs"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        queryset = self.get_queryset()
        tags_to_delete = queryset.filter(id__in=tag_ids)

        deleted_count = tags_to_delete.count()
        not_found_ids = set(tag_ids) - set(tags_to_delete.values_list("id", flat=True))

        # Perform deletion (will cascade ArtifactTag rows only)
        tags_to_delete.delete()

        response_data: dict = {
            "deleted_count": deleted_count,
            "requested_count": len(tag_ids),
        }

        if not_found_ids:
            response_data["not_found_ids"] = sorted([int(x) for x in not_found_ids])

        return Response(response_data, status=status.HTTP_200_OK)

    # Note: reveal_value belongs on ArtifactViewSet (moved below).


class ArtifactGlobalSearchView(APIView):
    """
    Global search across all artifacts owned by the authenticated user.

    Query params:
      - q: search string
      - kind: filter by kind (ENV_VAR|PROMPT|DOC_LINK)
      - environment: filter by environment (DEV|STAGING|PROD)
      - workspace: optional workspace id to scope results
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):  # type: ignore[override]
        q = (request.query_params.get("q") or "").strip()  # type: ignore
        kind = request.query_params.get("kind")  # type: ignore
        env = request.query_params.get("environment")  # type: ignore
        workspace_id = request.query_params.get("workspace")  # type: ignore

        if not hasattr(request.user, "uid"):
            return Response(
                {"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED
            )

        # Filter artifacts by ownership via workspace relation
        qs = Artifact.objects.select_related(
            "workspace", "workspace_env", "workspace_env__environment_type"
        ).filter(
            workspace__owner_uid=request.user.uid  # type: ignore
        )

        if workspace_id:
            try:
                wsid = int(workspace_id)
                qs = qs.filter(workspace_id=wsid)
            except ValueError:
                pass

        if kind:
            qs = qs.filter(kind=kind)
        if env:
            try:
                qs = qs.filter(workspace_env__environment_type__slug=env)
            except Exception:
                qs = qs.filter(environment=env)

        if q:
            from django.db.models import Q

            qs = qs.filter(
                Q(key__icontains=q)
                | Q(title__icontains=q)
                | Q(content__icontains=q)
                | Q(notes__icontains=q)
                | Q(url__icontains=q)
                | Q(tags__name__icontains=q)
            )

        # Order by most recently updated
        qs = qs.order_by("-updated_at")[:200]

        data = ArtifactSerializer(qs, many=True).data
        return Response({"results": data, "count": len(data)})


class DocsGlobalListView(APIView):
    """
    Aggregate DOC_LINK artifacts across all user workspaces.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):  # type: ignore[override]
        if not hasattr(request.user, "uid"):
            return Response(
                {"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED
            )

        links = (
            Artifact.objects.select_related("workspace")
            .filter(workspace__owner_uid=request.user.uid, kind="DOC_LINK")  # type: ignore
            .order_by("-updated_at")
        )
        data = ArtifactSerializer(links, many=True).data
        return Response({"results": data, "count": len(data)})
