"""
ViewSets for artifact management in the DEADLINE API.

This module provides RESTful API endpoints for artifact CRUD operations
with workspace-based nested routing, Firebase UID-based ownership,
and polymorphic artifact type support.
"""

from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from auth_firebase.permissions import IsOwner
from workspaces.models import Workspace

from .models import Artifact
from .serializers import ArtifactSerializer


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
    search_fields = ["key", "title", "content", "notes", "url"]
    ordering_fields = ["created_at", "updated_at", "kind", "environment"]
    ordering = ["-updated_at"]

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
                    "workspace"
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

    def get_queryset_filters(self):
        """Apply query parameter filters manually."""
        queryset = self.get_queryset()

        # Filter by kind
        kind = self.request.query_params.get("kind")  # type: ignore
        if kind:
            queryset = queryset.filter(kind=kind)

        # Filter by environment
        environment = self.request.query_params.get("environment")  # type: ignore
        if environment:
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

    @action(detail=True, methods=["post"])
    def duplicate_to_environment(self, request, *args, **kwargs):
        """
        Duplicate artifact to a different environment.

        Creates a copy of the artifact with the specified target environment
        while preserving all other data.
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

        # Create duplicate data
        duplicate_data = {
            "workspace": artifact.workspace.id,
            "kind": artifact.kind,
            "environment": target_environment,
            "notes": artifact.notes,
            "metadata": artifact.metadata,
        }

        # Add type-specific fields
        if artifact.kind == "ENV_VAR":
            duplicate_data.update(
                {
                    "key": artifact.key,
                    "value": artifact.value,
                }
            )
        elif artifact.kind == "PROMPT":
            duplicate_data.update(
                {
                    "title": artifact.title,
                    "content": artifact.content,
                }
            )
        elif artifact.kind == "DOC_LINK":
            duplicate_data.update(
                {
                    "title": artifact.title,
                    "url": artifact.url,
                }
            )

        serializer = self.get_serializer(data=duplicate_data)
        if serializer.is_valid():
            # Ensure workspace is set (serializer field is read-only)
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

    @action(detail=False, methods=["delete"])
    def bulk_delete(self, request, *args, **kwargs):
        """
        Delete multiple artifacts by IDs.

        Accepts an array of artifact IDs and deletes them if they
        belong to the workspace and user has permission.
        """
        artifact_ids = request.data.get("ids", [])

        if not isinstance(artifact_ids, list) or not artifact_ids:
            return Response(
                {"error": "Expected an array of artifact IDs"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Filter artifacts that exist and belong to this workspace
        queryset = self.get_queryset()
        artifacts_to_delete = queryset.filter(id__in=artifact_ids)

        deleted_count = artifacts_to_delete.count()
        not_found_ids = set(artifact_ids) - set(
            artifacts_to_delete.values_list("id", flat=True)
        )

        # Perform deletion
        artifacts_to_delete.delete()

        response_data: dict = {
            "deleted_count": deleted_count,
            "requested_count": len(artifact_ids),
        }

        if not_found_ids:
            response_data["not_found_ids"] = sorted([int(x) for x in not_found_ids])

        return Response(response_data, status=status.HTTP_200_OK)
