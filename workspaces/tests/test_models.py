"""
Tests for Workspace models.

These tests validate the Workspace model functionality including validation,
constraints, and Firebase UID-based ownership patterns.
"""

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from workspaces.models import Workspace


class WorkspaceModelTest(TestCase):
    """Test cases for the Workspace model."""

    def setUp(self):
        """Set up test data."""
        self.valid_owner_uid = "test_firebase_uid_123"
        self.valid_workspace_data = {
            "name": "Test Workspace",
            "description": "A test workspace for development",
            "owner_uid": self.valid_owner_uid,
        }

    def test_workspace_creation_success(self):
        """Test successful workspace creation."""
        workspace = Workspace.objects.create(**self.valid_workspace_data)

        self.assertEqual(workspace.name, "Test Workspace")
        self.assertEqual(workspace.description, "A test workspace for development")
        self.assertEqual(workspace.owner_uid, self.valid_owner_uid)
        self.assertIsNotNone(workspace.created_at)
        self.assertIsNotNone(workspace.updated_at)
        self.assertIsNotNone(workspace.id)

    def test_workspace_str_representation(self):
        """Test string representation of workspace."""
        workspace = Workspace.objects.create(**self.valid_workspace_data)
        expected_str = f"Test Workspace ({self.valid_owner_uid[:8]}...)"
        self.assertEqual(str(workspace), expected_str)

    def test_workspace_short_owner_uid(self):
        """Test short_owner_uid property."""
        workspace = Workspace.objects.create(**self.valid_workspace_data)
        expected_short = f"{self.valid_owner_uid[:8]}..."
        self.assertEqual(workspace.short_owner_uid, expected_short)

    def test_workspace_name_validation_empty(self):
        """Test validation fails for empty workspace name."""
        with self.assertRaises(ValidationError):
            workspace = Workspace(name="", owner_uid=self.valid_owner_uid)
            workspace.full_clean()

    def test_workspace_name_validation_whitespace_only(self):
        """Test validation fails for whitespace-only name."""
        with self.assertRaises(ValidationError):
            workspace = Workspace(name="   ", owner_uid=self.valid_owner_uid)
            workspace.full_clean()

    def test_workspace_name_validation_too_long(self):
        """Test validation fails for name exceeding 255 characters."""
        long_name = "a" * 256
        with self.assertRaises(ValidationError):
            workspace = Workspace(name=long_name, owner_uid=self.valid_owner_uid)
            workspace.full_clean()

    def test_workspace_name_validation_invalid_characters(self):
        """Test validation fails for invalid characters in name."""
        invalid_names = [
            "Test@Workspace",  # @ symbol
            "Test<Workspace>",  # < > symbols
            "Test|Workspace",  # | symbol
        ]

        for invalid_name in invalid_names:
            with self.assertRaises(ValidationError):
                workspace = Workspace(name=invalid_name, owner_uid=self.valid_owner_uid)
                workspace.full_clean()

    def test_workspace_name_validation_valid_characters(self):
        """Test validation passes for valid characters in name."""
        valid_names = [
            "Test Workspace",
            "Test-Workspace",
            "Test_Workspace",
            "Test.Workspace",
            "TestWorkspace123",
            "API Dashboard v2.0",
        ]

        for valid_name in valid_names:
            workspace = Workspace(
                name=valid_name,
                owner_uid=f"{self.valid_owner_uid}_{valid_name.replace(' ', '_')}",
            )
            workspace.full_clean()  # Should not raise ValidationError

    def test_workspace_owner_uid_validation_empty(self):
        """Test validation fails for empty owner UID."""
        with self.assertRaises(ValidationError):
            workspace = Workspace(name="Test Workspace", owner_uid="")
            workspace.full_clean()

    def test_workspace_owner_uid_validation_too_short(self):
        """Test validation fails for too short owner UID."""
        with self.assertRaises(ValidationError):
            workspace = Workspace(name="Test Workspace", owner_uid="ab")  # Too short
            workspace.full_clean()

    def test_unique_constraint_same_user_same_name(self):
        """Test unique constraint prevents duplicate workspace names for same user."""
        # Create first workspace
        Workspace.objects.create(**self.valid_workspace_data)

        # Try to create duplicate - should raise ValidationError due to our save() override
        with self.assertRaises(ValidationError):
            Workspace.objects.create(**self.valid_workspace_data)

    def test_unique_constraint_different_users_same_name(self):
        """Test different users can have workspaces with same name."""
        # Create first workspace
        Workspace.objects.create(**self.valid_workspace_data)

        # Create workspace with same name but different owner
        different_owner_data = self.valid_workspace_data.copy()
        different_owner_data["owner_uid"] = "different_firebase_uid_456"

        workspace2 = Workspace.objects.create(**different_owner_data)
        self.assertIsNotNone(workspace2.id)

    def test_workspace_ordering(self):
        """Test workspace ordering by updated_at desc, then name."""
        # Create workspaces with different names
        workspace1 = Workspace.objects.create(
            name="B Workspace", owner_uid=self.valid_owner_uid
        )
        workspace2 = Workspace.objects.create(
            name="A Workspace", owner_uid=self.valid_owner_uid + "2"
        )

        # Get all workspaces - should be ordered by updated_at desc, then name
        workspaces = list(Workspace.objects.all())
        self.assertEqual(len(workspaces), 2)
        # Most recently created should be first
        self.assertEqual(workspaces[0].id, workspace2.id)

    def test_description_optional(self):
        """Test description field is optional."""
        workspace_data = self.valid_workspace_data.copy()
        del workspace_data["description"]

        workspace = Workspace.objects.create(**workspace_data)
        self.assertEqual(workspace.description, "")

    def test_description_whitespace_cleaned(self):
        """Test description whitespace is cleaned."""
        workspace = Workspace.objects.create(
            name="Test Workspace",
            description="  Test description with whitespace  ",
            owner_uid=self.valid_owner_uid,
        )
        self.assertEqual(workspace.description, "Test description with whitespace")

