"""
Serializers for artifact models in the DEADLINE API.

This module defines serializers for converting polymorphic artifact models
to/from JSON representations for API responses with dynamic field handling.
"""

from rest_framework import serializers

from .models import Artifact


class ArtifactSerializer(serializers.ModelSerializer):
    """
    Dynamic serializer for polymorphic Artifact model.

    Handles serialization of artifact data with type-specific field
    inclusion based on artifact.kind (ENV_VAR/PROMPT/DOC_LINK).
    Provides validation and secure value handling.
    """

    # Read-only fields that should not be updated via API
    id = serializers.IntegerField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    workspace = serializers.PrimaryKeyRelatedField(read_only=True)

    # Workspace name for convenient reference
    workspace_name = serializers.CharField(source="workspace.name", read_only=True)

    # Type-specific fields - marked as not required to allow polymorphic usage
    key = serializers.CharField(required=False, allow_blank=True)
    value = serializers.CharField(required=False, allow_blank=True)
    title = serializers.CharField(required=False, allow_blank=True)
    content = serializers.CharField(required=False, allow_blank=True)
    url = serializers.URLField(required=False, allow_blank=True)

    class Meta:
        model = Artifact
        fields = [
            "id",
            "workspace",
            "workspace_name",
            "kind",
            "environment",
            "created_at",
            "updated_at",
            "notes",
            # Type-specific fields (all included, filtered in to_representation)
            "key",
            "value",
            "title",
            "content",
            "url",
            "metadata",
        ]

    def to_representation(self, instance):
        """
        Dynamic field representation based on artifact kind.

        Only includes relevant fields for each artifact type:
        - ENV_VAR: key, value, notes
        - PROMPT: title, content, notes
        - DOC_LINK: title, url, notes
        """
        data = super().to_representation(instance)

        if instance.kind == "ENV_VAR":
            # Remove unused fields for ENV_VAR
            data.pop("title", None)
            data.pop("content", None)
            data.pop("url", None)

            # Mask sensitive values in API responses for security
            if data.get("value"):
                data["value"] = "••••••"
                data["value_masked"] = True
            else:
                data["value_masked"] = False

        elif instance.kind == "PROMPT":
            # Remove unused fields for PROMPT
            data.pop("key", None)
            data.pop("value", None)
            data.pop("url", None)

        elif instance.kind == "DOC_LINK":
            # Remove unused fields for DOC_LINK
            data.pop("key", None)
            data.pop("value", None)
            data.pop("content", None)

        return data

    def validate(self, attrs):
        """
        Type-specific validation based on artifact kind.

        Ensures required fields are present and valid for each artifact type.
        """
        kind = attrs.get("kind")

        if kind == "ENV_VAR":
            if not attrs.get("key"):
                raise serializers.ValidationError({"key": "ENV_VAR requires a key"})
            if not attrs.get("value"):
                raise serializers.ValidationError({"value": "ENV_VAR requires a value"})
            # Clear unused fields
            attrs.pop("title", None)
            attrs.pop("content", None)
            attrs.pop("url", None)

        elif kind == "PROMPT":
            if not attrs.get("title"):
                raise serializers.ValidationError({"title": "PROMPT requires a title"})
            # Clear unused fields
            attrs.pop("key", None)
            attrs.pop("value", None)
            attrs.pop("url", None)

        elif kind == "DOC_LINK":
            if not attrs.get("title"):
                raise serializers.ValidationError(
                    {"title": "DOC_LINK requires a title"}
                )
            if not attrs.get("url"):
                raise serializers.ValidationError({"url": "DOC_LINK requires a URL"})
            # Clear unused fields
            attrs.pop("key", None)
            attrs.pop("value", None)
            attrs.pop("content", None)

        return attrs

    def validate_key(self, value):
        """Validate ENV_VAR key format."""
        if value and not value.replace("_", "").replace("-", "").isalnum():
            raise serializers.ValidationError(
                "Key must contain only alphanumeric characters, underscores, and hyphens"
            )
        return value

    def validate_environment(self, value):
        """Validate environment choice."""
        valid_environments = ["DEV", "STAGING", "PROD"]
        if value not in valid_environments:
            raise serializers.ValidationError(
                f'Environment must be one of: {", ".join(valid_environments)}'
            )
        return value
