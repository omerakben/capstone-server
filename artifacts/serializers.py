"""
Serializers for artifact models in the DEADLINE API.

This module defines serializers for converting polymorphic artifact models
to/from JSON representations for API responses with dynamic field handling.
"""

from django.db.models import QuerySet
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
        many=True,
        required=False,
        queryset=Tag.objects.none(),  # Will be set dynamically
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set tag queryset based on workspace context
        workspace = None
        inst = getattr(self, "instance", None)
        if inst is not None:
            if hasattr(inst, "workspace"):
                workspace = inst.workspace
            elif isinstance(inst, (list, tuple)) and inst:
                first = inst[0]
                if hasattr(first, "workspace"):
                    workspace = first.workspace
            elif isinstance(inst, QuerySet):
                try:
                    first = inst.first()
                    if first is not None and hasattr(first, "workspace"):
                        workspace = first.workspace
                except Exception:
                    pass
        if workspace is None and self.context.get("workspace"):
            workspace = self.context.get("workspace")

        if "tags" in self.fields:
            field = self.fields["tags"]
            # For many=True relations DRF wraps the relation as ManyRelatedField
            target = getattr(field, "child_relation", field)
            if workspace:
                target.queryset = Tag.objects.filter(workspace=workspace)
            else:
                # Fallback: use all tags (this shouldn't happen in normal operation)
                target.queryset = Tag.objects.all()

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

    def validate_tags(self, tags):
        """Validate that all tags belong to the artifact's workspace."""
        if not tags:
            return tags

        # Get workspace from context or instance
        workspace = self.context.get("workspace")
        if not workspace and self.instance:
            workspace = self.instance.workspace

        if not workspace:
            # If no workspace context, can't validate - let the view handle it
            return tags

        workspace_id = workspace.id if hasattr(workspace, "id") else workspace

        # Check all tags belong to the same workspace
        invalid_tags = [tag for tag in tags if tag.workspace_id != workspace_id]

        if invalid_tags:
            raise serializers.ValidationError(
                f"Tags must belong to the same workspace. Invalid tags: {[t.id for t in invalid_tags]}"
            )

        return tags

    def validate(self, attrs):
        """
        Type-specific validation based on artifact kind.

        Ensures required fields are present and valid for each artifact type.
        Also checks uniqueness constraints to provide better error messages.
        """
        kind = attrs.get("kind")

        if kind == "ENV_VAR":
            if not attrs.get("key"):
                raise serializers.ValidationError({"key": "ENV_VAR requires a key"})
            if not attrs.get("value"):
                raise serializers.ValidationError({"value": "ENV_VAR requires a value"})

            # Check uniqueness constraint for ENV_VAR
            workspace = self.context.get("workspace")
            if workspace:
                key = attrs.get("key")
                environment = attrs.get("environment")
                workspace_id = workspace.id if hasattr(workspace, "id") else workspace

                # Build queryset for existing artifacts with same key/env/workspace
                existing_qs = Artifact.objects.filter(
                    workspace_id=workspace_id,
                    kind="ENV_VAR",
                    key=key,
                    environment=environment,
                )

                # Exclude current instance if updating
                if self.instance:
                    existing_qs = existing_qs.exclude(id=self.instance.id)

                if existing_qs.exists():
                    raise serializers.ValidationError(
                        {
                            "key": f"An environment variable with key '{key}' already exists in {environment} environment."
                        }
                    )

            # Clear unused fields
            attrs.pop("title", None)
            attrs.pop("content", None)
            attrs.pop("url", None)

        elif kind == "PROMPT":
            if not attrs.get("title"):
                raise serializers.ValidationError({"title": "PROMPT requires a title"})

            # Check uniqueness constraint for PROMPT
            workspace = self.context.get("workspace")
            if workspace:
                title = attrs.get("title")
                environment = attrs.get("environment")
                workspace_id = workspace.id if hasattr(workspace, "id") else workspace

                existing_qs = Artifact.objects.filter(
                    workspace_id=workspace_id,
                    kind="PROMPT",
                    title=title,
                    environment=environment,
                )

                # Exclude current instance if updating
                if self.instance:
                    existing_qs = existing_qs.exclude(id=self.instance.id)

                if existing_qs.exists():
                    raise serializers.ValidationError(
                        {
                            "title": f"A prompt with title '{title}' already exists in {environment} environment."
                        }
                    )

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

            # Check uniqueness constraint for DOC_LINK
            workspace = self.context.get("workspace")
            if workspace:
                title = attrs.get("title")
                environment = attrs.get("environment")
                workspace_id = workspace.id if hasattr(workspace, "id") else workspace

                existing_qs = Artifact.objects.filter(
                    workspace_id=workspace_id,
                    kind="DOC_LINK",
                    title=title,
                    environment=environment,
                )

                # Exclude current instance if updating
                if self.instance:
                    existing_qs = existing_qs.exclude(id=self.instance.id)

                if existing_qs.exists():
                    raise serializers.ValidationError(
                        {
                            "title": f"A documentation link with title '{title}' already exists in {environment} environment."
                        }
                    )

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
        workspace = self.context.get("workspace")

        ws_id = None
        if workspace:
            ws_id = (
                workspace.id
                if hasattr(workspace, "id")
                else (int(workspace) if workspace else None)
            )

        self._apply_workspace_env_mapping(validated_data, ws_id)
        # Label handling
        self._apply_label_to_metadata_on_write(None, validated_data)
        artifact = super().create(validated_data)
        if tags:
            artifact.tags.set(tags)
        return artifact

    def update(self, instance, validated_data):
        tags = validated_data.pop("tags", None)

        # Validate tags belong to same workspace before updating
        if tags is not None:
            workspace_id = instance.workspace.id
            invalid_tags = [tag for tag in tags if tag.workspace_id != workspace_id]

            if invalid_tags:
                raise serializers.ValidationError(
                    {
                        "tags": f"Tags must belong to the same workspace. Invalid tags: {[t.id for t in invalid_tags]}"
                    }
                )

        # For partial updates of ENV_VAR: treat empty string value as "no change"
        if getattr(instance, "kind", None) == "ENV_VAR":
            if "value" in validated_data and (validated_data.get("value") == ""):
                validated_data.pop("value", None)

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
    usage_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Tag
        fields = [
            "id",
            "name",
            "workspace",
            "created_at",
            "updated_at",
            "usage_count",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def validate_name(self, value: str):
        """Validate tag name and ensure uniqueness within the workspace.

        - Trim whitespace
        - Disallow empty names
        - Enforce uniqueness per workspace (case-insensitive)
        """
        name = (value or "").strip()
        if not name:
            raise serializers.ValidationError("Name cannot be empty")

        workspace = self.context.get("workspace")
        if workspace is None:
            # Workspace is provided by the viewset; without it we can't enforce scope.
            return name

        qs = Tag.objects.filter(workspace=workspace)
        # Exclude current instance when updating
        if getattr(self, "instance", None) and self.instance:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.filter(name__iexact=name).exists():
            raise serializers.ValidationError(
                "A tag with this name already exists in this workspace"
            )

        return name
