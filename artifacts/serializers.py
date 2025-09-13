"""
Serializers for artifact models in the DEADLINE API.

This module defines serializers for converting polymorphic artifact models
to/from JSON representations for API responses with dynamic field handling.
"""

from rest_framework import serializers
from workspaces.models import WorkspaceEnvironment

from .models import Artifact, Tag


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
    # Virtual field mapped to metadata for DOC_LINK label
    label = serializers.CharField(required=False, allow_blank=True)
    # Tags: list of tag IDs writable, and expanded objects read-only companion
    tags = serializers.PrimaryKeyRelatedField(
        many=True, required=False, queryset=Tag.objects.all()
    )
    tag_objects = serializers.SerializerMethodField(read_only=True)

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
            "label",
            "tags",
            "tag_objects",
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
            # Surface label from metadata if present
            meta = getattr(instance, "metadata", {}) or {}
            if isinstance(meta, dict) and meta.get("label"):
                data["label"] = meta.get("label")

        return data

    def get_tag_objects(self, instance):
        tags_qs = getattr(instance, "tags", None)
        if not tags_qs:
            return []
        return [{"id": t.id, "name": t.name} for t in tags_qs.all().order_by("name")]

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
            # Move optional label into metadata
            label = attrs.pop("label", None)
            if label is not None:
                meta = attrs.get("metadata") or {}
                if not isinstance(meta, dict):
                    meta = {}
                # store trimmed label
                meta["label"] = str(label).strip()
                attrs["metadata"] = meta

        return attrs

    def _apply_workspace_env_mapping(self, validated_data, workspace_id: int | None):
        env_slug = validated_data.get("environment")
        if env_slug and workspace_id:
            we = (
                WorkspaceEnvironment.objects.select_related("environment_type")
                .filter(workspace_id=workspace_id, environment_type__slug=env_slug)
                .first()
            )
            if we:
                validated_data["workspace_env"] = we

    def _apply_label_to_metadata_on_write(self, instance, validated_data):
        label = validated_data.pop("label", None)
        if label is not None:
            meta = (
                instance.metadata if instance else validated_data.get("metadata")
            ) or {}
            if not isinstance(meta, dict):
                meta = {}
            meta["label"] = str(label).strip()
            validated_data["metadata"] = meta

    def create(self, validated_data):
        tags = validated_data.pop("tags", [])
        # Map slug to workspace_env
        workspace = self.context.get("workspace") or self.initial_data.get("workspace")
        ws_id = None
        try:
            ws_id = workspace.id if hasattr(workspace, "id") else int(workspace)
        except Exception:
            ws_id = None
        self._apply_workspace_env_mapping(validated_data, ws_id)
        # Label handling
        self._apply_label_to_metadata_on_write(None, validated_data)
        artifact = super().create(validated_data)
        if tags:
            artifact.tags.set(tags)
        return artifact

    def update(self, instance, validated_data):
        tags = validated_data.pop("tags", None)
        # Map slug to workspace_env
        ws_id = instance.workspace.id if instance and instance.workspace_id else None
        self._apply_workspace_env_mapping(validated_data, ws_id)
        # Label handling
        self._apply_label_to_metadata_on_write(instance, validated_data)
        artifact = super().update(instance, validated_data)
        if tags is not None:
            artifact.tags.set(tags)
        return artifact


class TagSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    workspace = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Tag
        fields = ["id", "name", "workspace", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]

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
