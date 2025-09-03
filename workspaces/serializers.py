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

    # Optional field for artifact counts (can be added via prefetch)
    artifact_counts = serializers.DictField(read_only=True, required=False)

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
