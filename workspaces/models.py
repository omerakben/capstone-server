"""
Workspace models for the DEADLINE developer command center.

This module contains models for managing user workspaces that organize artifacts
by project or domain with Firebase UID-based ownership.
"""

import re

from django.core.exceptions import ValidationError
from django.db import models


class Workspace(models.Model):
    """
    Workspace model for organizing artifacts by project or domain.

    Each workspace is owned by a Firebase user (identified by UID) and serves
    as a container for organizing related artifacts across different environments.
    """

    id = models.AutoField(primary_key=True)
    name = models.CharField(
        max_length=255,
        help_text="Workspace name (e.g., 'E-commerce API', 'Frontend Dashboard')",
    )
    description = models.TextField(
        blank=True, help_text="Optional description of the workspace purpose"
    )
    owner_uid = models.CharField(
        max_length=128, db_index=True, help_text="Firebase UID of the workspace owner"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at", "name"]
        indexes = [
            models.Index(fields=["owner_uid"]),
            models.Index(fields=["owner_uid", "-updated_at"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["owner_uid", "name"], name="unique_workspace_name_per_user"
            ),
        ]

    def clean(self):
        """Validate workspace data."""
        super().clean()

        # Validate name length and content
        if not self.name or not self.name.strip():
            raise ValidationError("Workspace name cannot be empty")

        # Ensure name is not too long after stripping
        self.name = self.name.strip()
        if len(self.name) > 255:
            raise ValidationError("Workspace name cannot exceed 255 characters")

        # Validate name contains valid characters (alphanumeric, spaces, hyphens, underscores)
        if not re.match(r"^[a-zA-Z0-9\s\-_\.]+$", self.name):
            raise ValidationError(
                "Workspace name can only contain letters, numbers, spaces, hyphens, underscores, and periods"
            )

        # Validate owner_uid format (Firebase UIDs are typically 28 chars, but allow up to 128)
        if not self.owner_uid or len(self.owner_uid) < 3:
            raise ValidationError("Invalid owner UID format")

        # Clean description
        if self.description:
            self.description = self.description.strip()

    def save(self, *args, **kwargs):
        """Override save to ensure validation runs."""
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.name} ({self.owner_uid[:8] if self.owner_uid else 'Unknown'}...)"

    def __repr__(self) -> str:
        return (
            f"Workspace(id={self.id}, name='{self.name}', owner_uid='{self.owner_uid}')"
        )

    @property
    def short_owner_uid(self) -> str:
        """Return shortened owner UID for display purposes."""
        if not self.owner_uid:
            return "Unknown"
        return (
            f"{self.owner_uid[:8]}..."
            if len(str(self.owner_uid)) > 8
            else str(self.owner_uid)
        )

    def delete(self, *args, **kwargs):
        """
        Ensure full cleanup on workspace deletion.

        Artifacts reference WorkspaceEnvironment with PROTECT to prevent
        accidental environment removal when artifacts exist. When deleting a
        workspace, we want all related data removed. Deleting artifacts first
        avoids PROTECT conflicts, then we proceed with the normal cascade which
        removes WorkspaceEnvironment rows and the workspace itself.
        """
        # Delete related artifacts up-front to avoid PROTECT via workspace_env
        try:
            self.artifacts.all().delete()
        except Exception:  # best-effort cleanup; continue with deletion
            pass
        # Proceed with default deletion (will cascade workspace_environments)
        return super().delete(*args, **kwargs)


class EnvironmentType(models.Model):
    """
    Master list of environment types (e.g., DEV, STAGING, PROD).

    Seeded rows define the canonical set of environments a workspace can enable.
    """

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=20, unique=True)
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["display_order", "name"]

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{self.name} ({self.slug})"


class WorkspaceEnvironment(models.Model):
    """
    Join entity to represent which environments are enabled for a workspace.

    This enables a many-to-many relationship between Workspace and EnvironmentType.
    """

    id = models.AutoField(primary_key=True)
    workspace = models.ForeignKey(
        Workspace, on_delete=models.CASCADE, related_name="workspace_environments"
    )
    environment_type = models.ForeignKey(
        EnvironmentType,
        on_delete=models.CASCADE,
        related_name="workspace_environments",
    )

    class Meta:
        unique_together = ("workspace", "environment_type")
        indexes = [
            models.Index(fields=["workspace", "environment_type"]),
        ]
        ordering = ["workspace_id", "environment_type_id"]

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{self.workspace_id}-{self.environment_type_id}"
