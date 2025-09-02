"""
Django admin configuration for Workspace models.

This module configures the Django admin interface for managing workspaces
during development and testing.
"""

from django.contrib import admin

from .models import Workspace


@admin.register(Workspace)
class WorkspaceAdmin(admin.ModelAdmin):
    """Admin interface for Workspace model."""

    list_display = ["name", "short_owner_uid", "created_at", "updated_at"]
    list_filter = ["created_at", "updated_at"]
    search_fields = ["name", "owner_uid", "description"]
    readonly_fields = ["id", "created_at", "updated_at"]
    ordering = ["-updated_at", "name"]

    fieldsets = (
        ("Basic Information", {"fields": ("name", "description")}),
        ("Ownership", {"fields": ("owner_uid",)}),
        (
            "Metadata",
            {"fields": ("id", "created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def short_owner_uid(self, obj):
        """Display shortened owner UID in admin list."""
        return obj.short_owner_uid

    # Set the column header for the admin list
    short_owner_uid.short_description = "Owner UID"  # type: ignore
