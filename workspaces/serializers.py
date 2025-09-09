"""
Serializers for workspace models in the DEADLINE API.

This module defines serializers for converting workspace models
to/from JSON representations for API responses.
"""

from rest_framework import serializers

from .models import Workspace


class WorkspaceSerializer(serializers.ModelSerializer):
    """
    Serializer for Workspace model.

    Handles serialization of workspace data with automatic
    timestamp formatting and validation.
    """

    # Read-only fields that should not be updated via API
    id = serializers.IntegerField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    owner_uid = serializers.CharField(read_only=True)

    # Artifact counts computed from prefetched artifacts
    artifact_counts = serializers.SerializerMethodField()
    # Enabled environments for this workspace (M2M via WorkspaceEnvironment)
    enabled_environments = serializers.SerializerMethodField()

    class Meta:
        model = Workspace
        fields = [
            "id",
            "name",
            "description",
            "owner_uid",
            "created_at",
            "updated_at",
            "artifact_counts",
            "enabled_environments",
        ]

    def validate_name(self, value):
        """Validate workspace name."""
        if not value.strip():
            raise serializers.ValidationError("Workspace name cannot be empty")
        return value.strip()

    def get_artifact_counts(self, obj):
        """
        Compute artifact counts by type and environment.

        Returns structured counts leveraging prefetched artifacts
        to avoid additional database queries.
        """
        # Use prefetched artifacts for efficient computation
        artifacts = obj.artifacts.all()

        # Compute total count
        total = len(artifacts)

        # Compute counts by artifact type
        by_type = {
            "ENV_VAR": len([a for a in artifacts if a.kind == "ENV_VAR"]),
            "PROMPT": len([a for a in artifacts if a.kind == "PROMPT"]),
            "DOC_LINK": len([a for a in artifacts if a.kind == "DOC_LINK"]),
        }

        # Compute counts by environment (prefer workspace_env join when available)
        def env_slug(a):
            try:
                we = getattr(a, "workspace_env", None)
                if we and getattr(we, "environment_type", None):
                    return getattr(we.environment_type, "slug", None) or a.environment
            except Exception:
                pass
            return a.environment

        by_environment = {"DEV": 0, "STAGING": 0, "PROD": 0}
        for a in artifacts:
            slug = env_slug(a) or ""
            if slug in by_environment:
                by_environment[slug] += 1

        return {
            "total": total,
            "by_type": by_type,
            "by_environment": by_environment,
        }

    def get_enabled_environments(self, obj):
        """Return enabled environments for this workspace as a list of dicts."""
        # Allow views to opt-out to avoid extra queries in list endpoints
        if not self.context.get("include_enabled_environments", True):
            return []
        try:
            wes_mgr = getattr(obj, "workspace_environments", None)
            if wes_mgr is None:
                return []

            # If prefetched via get_queryset(), use the cached objects to avoid
            # additional queries. Otherwise, fetch with select_related.
            prefetched = getattr(obj, "_prefetched_objects_cache", {}) or {}
            if "workspace_environments" in prefetched:
                wes = prefetched["workspace_environments"]
            else:
                wes = wes_mgr.select_related("environment_type").all()

            items = []
            for we in wes:
                et = getattr(we, "environment_type", None)
                if not et:
                    continue
                items.append(
                    {
                        "slug": et.slug,
                        "name": et.name,
                        "display_order": et.display_order,
                    }
                )
            # Sort by display_order then name for stability
            items.sort(key=lambda x: (x.get("display_order", 0), x.get("name", "")))
            return items
        except Exception:
            return []
