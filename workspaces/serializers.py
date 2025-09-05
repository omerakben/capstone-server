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

        # Compute counts by environment
        by_environment = {
            "DEV": len([a for a in artifacts if a.environment == "DEV"]),
            "STAGING": len([a for a in artifacts if a.environment == "STAGING"]),
            "PROD": len([a for a in artifacts if a.environment == "PROD"]),
        }

        return {
            "total": total,
            "by_type": by_type,
            "by_environment": by_environment,
        }
