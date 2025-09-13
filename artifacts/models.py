import re

from django.core.exceptions import ValidationError
from django.db import models


def validate_env_var_key(value):
    """Validate ENV_VAR keys are uppercase alphanumeric with underscores"""
    if not re.match(r"^[A-Z0-9_]+$", value):
        raise ValidationError(
            "ENV_VAR key must be uppercase alphanumeric with underscores"
        )


def validate_prompt_content_length(value):
    """Validate PROMPT content doesn't exceed 10,000 characters"""
    if len(value) > 10000:
        raise ValidationError("PROMPT content cannot exceed 10,000 characters")


class Artifact(models.Model):
    """
    Polymorphic model for storing different types of developer artifacts.

    Supports three artifact types:
    - ENV_VAR: Environment variables with key/value pairs
    - PROMPT: AI/code prompts with title and content
    - DOC_LINK: Documentation links with title and URL

    Each artifact belongs to a workspace and has environment awareness
    (Dev/Staging/Prod) as a user feature for organization.
    """

    ARTIFACT_KINDS = [
        ("ENV_VAR", "Environment Variable"),
        ("PROMPT", "Code/AI Prompt"),
        ("DOC_LINK", "Documentation Link"),
    ]

    ENVIRONMENT_CHOICES = [
        ("DEV", "Development"),
        ("STAGING", "Staging"),
        ("PROD", "Production"),
    ]

    # Core fields
    id = models.AutoField(primary_key=True)
    workspace = models.ForeignKey(
        "workspaces.Workspace", on_delete=models.CASCADE, related_name="artifacts"
    )
    kind = models.CharField(max_length=20, choices=ARTIFACT_KINDS, db_index=True)
    environment = models.CharField(
        max_length=20, choices=ENVIRONMENT_CHOICES, default="DEV"
    )
    # New: link to WorkspaceEnvironment (many-to-many workspace↔environment)
    # Kept nullable during migration to backfill safely; later can be non-null
    workspace_env = models.ForeignKey(
        "workspaces.WorkspaceEnvironment",
        on_delete=models.PROTECT,
        related_name="artifacts",
        null=True,
        blank=True,
    )

    # Common fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)

    # Type-specific fields (polymorphic design)
    # ENV_VAR fields
    key = models.CharField(max_length=255, blank=True)  # For ENV_VAR
    value = models.TextField(blank=True)  # For ENV_VAR

    # PROMPT and DOC_LINK fields
    title = models.CharField(max_length=255, blank=True)  # For PROMPT, DOC_LINK

    # PROMPT fields
    content = models.TextField(blank=True)  # For PROMPT (markdown)

    # DOC_LINK fields
    url = models.URLField(blank=True)  # For DOC_LINK

    # Metadata storage for additional fields
    metadata = models.JSONField(default=dict, blank=True)

    # Many-to-Many: Tags (explicit through table for uniqueness & auditing)
    tags = models.ManyToManyField(
        "Tag",
        through="ArtifactTag",
        related_name="artifacts",
        blank=True,
    )

    class Meta:
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["workspace", "kind"]),
            models.Index(fields=["workspace", "environment"]),
            models.Index(fields=["workspace_env"]),
            models.Index(fields=["kind", "-updated_at"]),
            models.Index(fields=["workspace", "kind", "environment"]),
        ]
        constraints = [
            # Unique constraints for different artifact types
            models.UniqueConstraint(
                fields=["workspace", "kind", "key", "environment"],
                condition=models.Q(kind="ENV_VAR") & ~models.Q(key=""),
                name="unique_env_var_key_per_workspace_environment",
            ),
            models.UniqueConstraint(
                fields=["workspace", "kind", "title", "environment"],
                condition=models.Q(kind__in=["PROMPT", "DOC_LINK"])
                & ~models.Q(title=""),
                name="unique_title_per_workspace_environment_and_kind",
            ),
        ]

    def clean(self):
        """Type-specific validation"""
        super().clean()

        if self.kind == "ENV_VAR":
            if not self.key:
                raise ValidationError({"key": "ENV_VAR requires a key"})
            validate_env_var_key(self.key)
            if not self.value:
                raise ValidationError({"value": "ENV_VAR requires a value"})

        elif self.kind == "PROMPT":
            if not self.title:
                raise ValidationError({"title": "PROMPT requires a title"})
            if self.content:
                validate_prompt_content_length(self.content)

        elif self.kind == "DOC_LINK":
            if not self.title:
                raise ValidationError({"title": "DOC_LINK requires a title"})
            if not self.url:
                raise ValidationError({"url": "DOC_LINK requires a URL"})

    def save(self, *args, **kwargs):
        """Override save to call full_clean() for validation"""
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        """String representation based on artifact type"""
        if self.kind == "ENV_VAR":
            return f"{self.key} ({self.environment})"
        elif self.kind == "PROMPT":
            return f"{self.title} (Prompt - {self.environment})"
        elif self.kind == "DOC_LINK":
            return f"{self.title} (Link - {self.environment})"
        return f"Artifact {self.id} ({self.kind})"

    @property
    def display_value(self):
        """Returns the primary display value for this artifact"""
        if self.kind == "ENV_VAR":
            return self.value or ""
        elif self.kind == "PROMPT":
            content = str(self.content or "")
            return (content[:100] + "...") if len(content) > 100 else content
        elif self.kind == "DOC_LINK":
            return self.url or ""
        return ""

    @property
    def primary_identifier(self):
        """Returns the primary identifier for this artifact"""
        if self.kind == "ENV_VAR":
            return self.key
        elif self.kind in ["PROMPT", "DOC_LINK"]:
            return self.title
        return f"Artifact {self.id}"

    # Declared after class so Tag is defined below; patched back in via string reference if necessary.
    # (Will be attached later if not already present by migration time.)


class Tag(models.Model):
    """Tag for grouping artifacts (Many-to-Many with Artifact via ArtifactTag)."""

    id = models.AutoField(primary_key=True)
    workspace = models.ForeignKey(
        "workspaces.Workspace", on_delete=models.CASCADE, related_name="tags"
    )
    name = models.CharField(max_length=80)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("workspace", "name")
        indexes = [
            models.Index(fields=["workspace", "name"]),
        ]
        ordering = ["name"]

    def __str__(self):  # pragma: no cover - trivial
        return f"{self.name}" if self.name else "Tag"


class ArtifactTag(models.Model):
    """Explicit through table for Artifact ↔ Tag Many-to-Many relation."""

    id = models.AutoField(primary_key=True)
    artifact = models.ForeignKey(
        Artifact, on_delete=models.CASCADE, related_name="artifact_tags"
    )
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name="artifact_tags")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("artifact", "tag")
        indexes = [
            models.Index(fields=["artifact", "tag"]),
            models.Index(fields=["tag", "artifact"]),
        ]
        ordering = ["artifact_id", "tag_id"]

    def __str__(self):  # pragma: no cover - trivial
        return "ArtifactTag"
