"""
Comprehensive tests for Workspace ViewSet API endpoints.

Tests cover authentication, permissions, CRUD operations, artifact count
functionality, and performance optimizations.
"""

from unittest.mock import MagicMock, patch

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from artifacts.models import Artifact
from workspaces.models import Workspace


class WorkspaceViewSetTest(APITestCase):
    """Test Workspace ViewSet API endpoints with Firebase authentication."""

    def setUp(self):
        """Set up test data and mock Firebase authentication."""
        self.test_user_uid = "test_user_uid_123"
        self.other_user_uid = "other_user_uid_456"

        # Create test workspaces
        self.user_workspace = Workspace.objects.create(
            name="User Workspace",
            description="Test workspace for authenticated user",
            owner_uid=self.test_user_uid,
        )

        self.other_workspace = Workspace.objects.create(
            name="Other Workspace",
            description="Test workspace for different user",
            owner_uid=self.other_user_uid,
        )

        # Create test artifacts for count verification
        self.create_test_artifacts()

    def create_test_artifacts(self):
        """Create sample artifacts for testing artifact counts."""
        # ENV_VAR artifacts in different environments
        Artifact.objects.create(
            workspace=self.user_workspace,
            kind="ENV_VAR",
            environment="DEV",
            key="API_KEY",
            value="dev_api_key",
        )
        Artifact.objects.create(
            workspace=self.user_workspace,
            kind="ENV_VAR",
            environment="PROD",
            key="API_KEY",
            value="prod_api_key",
        )

        # PROMPT artifacts
        Artifact.objects.create(
            workspace=self.user_workspace,
            kind="PROMPT",
            environment="DEV",
            title="Bug Report Template",
            content="Report bug: {{description}}",
        )

        # DOC_LINK artifacts
        Artifact.objects.create(
            workspace=self.user_workspace,
            kind="DOC_LINK",
            environment="DEV",
            title="Django Docs",
            url="https://docs.djangoproject.com",
        )

    def authenticate_user(self, uid=None):
        """Helper method to authenticate user with mock Firebase token."""
        test_uid = uid or self.test_user_uid
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer fake_token_{test_uid}")

    @patch("auth_firebase.authentication.firebase_auth.verify_id_token")
    def test_list_workspaces_authenticated(self, mock_verify_token):
        """Test that authenticated users can list their workspaces."""
        mock_verify_token.return_value = {"uid": self.test_user_uid}
        self.authenticate_user()

        response = self.client.get("/api/v1/workspaces/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["name"], "User Workspace")
        self.assertEqual(response.data["results"][0]["owner_uid"], self.test_user_uid)

    def test_list_workspaces_unauthenticated(self):
        """Test that unauthenticated users cannot list workspaces."""
        response = self.client.get("/api/v1/workspaces/")

        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    @patch("auth_firebase.authentication.firebase_auth.verify_id_token")
    def test_workspace_isolation_by_owner(self, mock_verify_token):
        """Test that users can only see their own workspaces."""
        mock_verify_token.return_value = {"uid": self.test_user_uid}
        self.authenticate_user()

        response = self.client.get("/api/v1/workspaces/")

        # Should only see user's workspace, not other user's workspace
        self.assertEqual(len(response.data["results"]), 1)
        workspace_names = [w["name"] for w in response.data["results"]]
        self.assertIn("User Workspace", workspace_names)
        self.assertNotIn("Other Workspace", workspace_names)

    @patch("auth_firebase.authentication.firebase_auth.verify_id_token")
    def test_create_workspace(self, mock_verify_token):
        """Test workspace creation with automatic owner_uid assignment."""
        mock_verify_token.return_value = {"uid": self.test_user_uid}
        self.authenticate_user()

        workspace_data = {
            "name": "New Project Workspace",
            "description": "A new workspace for testing",
        }

        response = self.client.post("/api/v1/workspaces/", workspace_data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "New Project Workspace")
        self.assertEqual(response.data["owner_uid"], self.test_user_uid)

        # Verify workspace was created in database
        workspace = Workspace.objects.get(id=response.data["id"])
        self.assertEqual(workspace.owner_uid, self.test_user_uid)

    @patch("auth_firebase.authentication.firebase_auth.verify_id_token")
    def test_create_workspace_validation(self, mock_verify_token):
        """Test workspace creation validation (empty name)."""
        mock_verify_token.return_value = {"uid": self.test_user_uid}
        self.authenticate_user()

        workspace_data = {
            "name": "   ",  # Empty name after strip
            "description": "Test description",
        }

        response = self.client.post("/api/v1/workspaces/", workspace_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data)

    @patch("auth_firebase.authentication.firebase_auth.verify_id_token")
    def test_retrieve_workspace(self, mock_verify_token):
        """Test retrieving a specific workspace."""
        mock_verify_token.return_value = {"uid": self.test_user_uid}
        self.authenticate_user()

        response = self.client.get(f"/api/v1/workspaces/{self.user_workspace.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "User Workspace")
        self.assertEqual(response.data["id"], self.user_workspace.id)

    @patch("auth_firebase.authentication.firebase_auth.verify_id_token")
    def test_retrieve_other_user_workspace_forbidden(self, mock_verify_token):
        """Test that users cannot retrieve other users' workspaces."""
        mock_verify_token.return_value = {"uid": self.test_user_uid}
        self.authenticate_user()

        response = self.client.get(f"/api/v1/workspaces/{self.other_workspace.id}/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch("auth_firebase.authentication.firebase_auth.verify_id_token")
    def test_update_workspace(self, mock_verify_token):
        """Test updating workspace details."""
        mock_verify_token.return_value = {"uid": self.test_user_uid}
        self.authenticate_user()

        update_data = {
            "name": "Updated Workspace Name",
            "description": "Updated description",
        }

        response = self.client.patch(
            f"/api/v1/workspaces/{self.user_workspace.id}/", update_data
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Updated Workspace Name")

        # Verify update in database
        self.user_workspace.refresh_from_db()
        self.assertEqual(self.user_workspace.name, "Updated Workspace Name")

    @patch("auth_firebase.authentication.firebase_auth.verify_id_token")
    def test_delete_workspace(self, mock_verify_token):
        """Test workspace deletion."""
        mock_verify_token.return_value = {"uid": self.test_user_uid}
        self.authenticate_user()

        response = self.client.delete(f"/api/v1/workspaces/{self.user_workspace.id}/")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify workspace was deleted
        self.assertFalse(Workspace.objects.filter(id=self.user_workspace.id).exists())

    @patch("auth_firebase.authentication.firebase_auth.verify_id_token")
    def test_artifact_counts_accuracy(self, mock_verify_token):
        """Test that artifact_counts field returns accurate counts."""
        mock_verify_token.return_value = {"uid": self.test_user_uid}
        self.authenticate_user()

        response = self.client.get(f"/api/v1/workspaces/{self.user_workspace.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        artifact_counts = response.data["artifact_counts"]

        # Verify total count
        self.assertEqual(artifact_counts["total"], 4)

        # Verify counts by type
        self.assertEqual(artifact_counts["by_type"]["ENV_VAR"], 2)
        self.assertEqual(artifact_counts["by_type"]["PROMPT"], 1)
        self.assertEqual(artifact_counts["by_type"]["DOC_LINK"], 1)

        # Verify counts by environment
        self.assertEqual(artifact_counts["by_environment"]["DEV"], 3)
        self.assertEqual(artifact_counts["by_environment"]["STAGING"], 0)
        self.assertEqual(artifact_counts["by_environment"]["PROD"], 1)

    @patch("auth_firebase.authentication.firebase_auth.verify_id_token")
    def test_empty_workspace_artifact_counts(self, mock_verify_token):
        """Test artifact counts for workspace with no artifacts."""
        mock_verify_token.return_value = {"uid": self.test_user_uid}
        self.authenticate_user()

        # Create empty workspace
        empty_workspace = Workspace.objects.create(
            name="Empty Workspace", owner_uid=self.test_user_uid
        )

        response = self.client.get(f"/api/v1/workspaces/{empty_workspace.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        artifact_counts = response.data["artifact_counts"]

        # Verify all counts are zero
        self.assertEqual(artifact_counts["total"], 0)
        self.assertEqual(artifact_counts["by_type"]["ENV_VAR"], 0)
        self.assertEqual(artifact_counts["by_type"]["PROMPT"], 0)
        self.assertEqual(artifact_counts["by_type"]["DOC_LINK"], 0)
        self.assertEqual(artifact_counts["by_environment"]["DEV"], 0)
        self.assertEqual(artifact_counts["by_environment"]["STAGING"], 0)
        self.assertEqual(artifact_counts["by_environment"]["PROD"], 0)

    @patch("auth_firebase.authentication.firebase_auth.verify_id_token")
    def test_artifact_counts_with_multiple_workspaces(self, mock_verify_token):
        """Test artifact counts don't leak between workspaces."""
        mock_verify_token.return_value = {"uid": self.test_user_uid}
        self.authenticate_user()

        # Create second workspace for same user
        second_workspace = Workspace.objects.create(
            name="Second Workspace", owner_uid=self.test_user_uid
        )

        # Add artifact to second workspace
        Artifact.objects.create(
            workspace=second_workspace,
            kind="ENV_VAR",
            environment="DEV",
            key="SECOND_KEY",
            value="second_value",
        )

        # Test first workspace counts haven't changed
        response1 = self.client.get(f"/api/v1/workspaces/{self.user_workspace.id}/")
        self.assertEqual(response1.data["artifact_counts"]["total"], 4)

        # Test second workspace has correct count
        response2 = self.client.get(f"/api/v1/workspaces/{second_workspace.id}/")
        self.assertEqual(response2.data["artifact_counts"]["total"], 1)

    @patch("auth_firebase.authentication.firebase_auth.verify_id_token")
    def test_performance_optimization_with_prefetch(self, mock_verify_token):
        """Test that prefetch_related optimizes database queries."""
        mock_verify_token.return_value = {"uid": self.test_user_uid}
        self.authenticate_user()

        # This test verifies that we're using prefetch_related correctly
        # The ViewSet should use prefetch_related('artifacts') to avoid N+1 queries
        with self.assertNumQueries(
            3
        ):  # 1 for count, 1 for workspace, 1 for prefetched artifacts
            response = self.client.get("/api/v1/workspaces/")

            # Access artifact_counts to ensure computation happens
            for workspace in response.data["results"]:
                _ = workspace["artifact_counts"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch("auth_firebase.authentication.firebase_auth.verify_id_token")
    def test_workspace_ordering(self, mock_verify_token):
        """Test that workspaces are returned in the correct order."""
        mock_verify_token.return_value = {"uid": self.test_user_uid}
        self.authenticate_user()

        # Create additional workspace to test ordering
        newer_workspace = Workspace.objects.create(
            name="Newer Workspace", owner_uid=self.test_user_uid
        )

        response = self.client.get("/api/v1/workspaces/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        workspaces = response.data["results"]

        # Should be ordered by -updated_at, name (from Workspace.Meta.ordering)
        # Newer workspace should come first since it was created later
        self.assertEqual(workspaces[0]["name"], "Newer Workspace")
        self.assertEqual(workspaces[1]["name"], "User Workspace")
