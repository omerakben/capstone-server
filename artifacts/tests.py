from unittest.mock import patch

from artifacts.models import (
    Artifact,
    ArtifactTag,
    Tag,
    validate_env_var_key,
    validate_prompt_content_length,
)
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase
from workspaces.models import Workspace


class ArtifactModelTest(TestCase):
    """Test cases for the polymorphic Artifact model"""

    def setUp(self):
        """Set up test workspace for artifact testing"""
        self.workspace = Workspace.objects.create(
            name="Test Workspace",
            description="Test workspace for artifact validation",
            owner_uid="test_user_123",
        )

    def test_env_var_creation_success(self):
        """Test successful creation of ENV_VAR artifact"""
        env_var = Artifact.objects.create(
            workspace=self.workspace,
            kind="ENV_VAR",
            environment="DEV",
            key="TEST_API_KEY",
            value="sample_value_123",
            notes="Test environment variable",
        )

        self.assertEqual(env_var.kind, "ENV_VAR")
        self.assertEqual(env_var.key, "TEST_API_KEY")
        self.assertEqual(env_var.value, "sample_value_123")
        self.assertEqual(env_var.environment, "DEV")
        self.assertEqual(str(env_var), "TEST_API_KEY (DEV)")

    def test_prompt_creation_success(self):
        """Test successful creation of PROMPT artifact"""
        prompt = Artifact.objects.create(
            workspace=self.workspace,
            kind="PROMPT",
            environment="DEV",
            title="Bug Report Template",
            content="## Bug Description\n\nProvide details...",
            notes="Standard bug report template",
        )

        self.assertEqual(prompt.kind, "PROMPT")
        self.assertEqual(prompt.title, "Bug Report Template")
        self.assertEqual(prompt.environment, "DEV")
        self.assertEqual(str(prompt), "Bug Report Template (Prompt - DEV)")

    def test_doc_link_creation_success(self):
        """Test successful creation of DOC_LINK artifact"""
        doc_link = Artifact.objects.create(
            workspace=self.workspace,
            kind="DOC_LINK",
            environment="PROD",
            title="Django REST Framework Documentation",
            url="https://www.django-rest-framework.org/",
            notes="Official DRF documentation",
        )

        self.assertEqual(doc_link.kind, "DOC_LINK")
        self.assertEqual(doc_link.title, "Django REST Framework Documentation")
        self.assertEqual(doc_link.url, "https://www.django-rest-framework.org/")
        self.assertEqual(doc_link.environment, "PROD")
        self.assertEqual(
            str(doc_link), "Django REST Framework Documentation (Link - PROD)"
        )

    def test_env_var_validation_missing_key(self):
        """Test ENV_VAR validation fails when key is missing"""
        with self.assertRaises(ValidationError) as context:
            artifact = Artifact(
                workspace=self.workspace,
                kind="ENV_VAR",
                environment="DEV",
                value="some_value",
                # key is missing
            )
            artifact.full_clean()

        self.assertIn("key", context.exception.message_dict)
        self.assertIn(
            "ENV_VAR requires a key", str(context.exception.message_dict["key"])
        )

    def test_env_var_validation_missing_value(self):
        """Test ENV_VAR validation fails when value is missing"""
        with self.assertRaises(ValidationError) as context:
            artifact = Artifact(
                workspace=self.workspace,
                kind="ENV_VAR",
                environment="DEV",
                key="TEST_KEY",
                # value is missing
            )
            artifact.full_clean()

        self.assertIn("value", context.exception.message_dict)
        self.assertIn(
            "ENV_VAR requires a value", str(context.exception.message_dict["value"])
        )

    def test_env_var_key_format_validation(self):
        """Test ENV_VAR key format validation"""
        # Test invalid key format (lowercase)
        with self.assertRaises(ValidationError):
            validate_env_var_key("invalid_key")

        # Test invalid key format (special characters)
        with self.assertRaises(ValidationError):
            validate_env_var_key("INVALID-KEY")

        # Test valid key format
        try:
            validate_env_var_key("VALID_API_KEY_123")
        except ValidationError:
            self.fail("validate_env_var_key raised ValidationError for valid key")

    def test_prompt_validation_missing_title(self):
        """Test PROMPT validation fails when title is missing"""
        with self.assertRaises(ValidationError) as context:
            artifact = Artifact(
                workspace=self.workspace,
                kind="PROMPT",
                environment="DEV",
                content="Some content",
                # title is missing
            )
            artifact.full_clean()

        self.assertIn("title", context.exception.message_dict)
        self.assertIn(
            "PROMPT requires a title", str(context.exception.message_dict["title"])
        )

    def test_prompt_content_length_validation(self):
        """Test PROMPT content length validation"""
        long_content = "x" * 10001  # Exceeds 10,000 character limit

        with self.assertRaises(ValidationError):
            validate_prompt_content_length(long_content)

        # Test valid content length
        valid_content = "x" * 5000
        try:
            validate_prompt_content_length(valid_content)
        except ValidationError:
            self.fail(
                "validate_prompt_content_length raised ValidationError for valid content"
            )

    def test_doc_link_validation_missing_title(self):
        """Test DOC_LINK validation fails when title is missing"""
        with self.assertRaises(ValidationError) as context:
            artifact = Artifact(
                workspace=self.workspace,
                kind="DOC_LINK",
                environment="DEV",
                url="https://example.com",
                # title is missing
            )
            artifact.full_clean()

        self.assertIn("title", context.exception.message_dict)
        self.assertIn(
            "DOC_LINK requires a title", str(context.exception.message_dict["title"])
        )

    def test_doc_link_validation_missing_url(self):
        """Test DOC_LINK validation fails when URL is missing"""
        with self.assertRaises(ValidationError) as context:
            artifact = Artifact(
                workspace=self.workspace,
                kind="DOC_LINK",
                environment="DEV",
                title="Test Documentation",
                # url is missing
            )
            artifact.full_clean()

        self.assertIn("url", context.exception.message_dict)
        self.assertIn(
            "DOC_LINK requires a URL", str(context.exception.message_dict["url"])
        )

    def test_unique_constraint_env_var_key_per_workspace_environment(self):
        """Test unique constraint for ENV_VAR keys per workspace/environment"""
        # Create first ENV_VAR
        Artifact.objects.create(
            workspace=self.workspace,
            kind="ENV_VAR",
            environment="DEV",
            key="DUPLICATE_KEY",
            value="value1",
        )

        # Try to create duplicate ENV_VAR with same key in same workspace/environment
        # This should raise ValidationError because we override save() to call full_clean()
        with self.assertRaises(ValidationError) as context:
            Artifact.objects.create(
                workspace=self.workspace,
                kind="ENV_VAR",
                environment="DEV",
                key="DUPLICATE_KEY",
                value="value2",
            )

        # Check that the error message contains constraint information
        self.assertIn(
            "unique_env_var_key_per_workspace_environment", str(context.exception)
        )

    def test_unique_constraint_allows_same_key_different_environment(self):
        """Test that same ENV_VAR key is allowed in different environments"""
        # Create ENV_VAR in DEV environment
        env_var_dev = Artifact.objects.create(
            workspace=self.workspace,
            kind="ENV_VAR",
            environment="DEV",
            key="SAME_KEY",
            value="dev_value",
        )

        # Create ENV_VAR with same key in PROD environment (should succeed)
        env_var_prod = Artifact.objects.create(
            workspace=self.workspace,
            kind="ENV_VAR",
            environment="PROD",
            key="SAME_KEY",
            value="prod_value",
        )

        self.assertEqual(env_var_dev.key, env_var_prod.key)
        self.assertNotEqual(env_var_dev.environment, env_var_prod.environment)

    def test_unique_constraint_prompt_title_per_workspace_environment(self):
        """Test unique constraint for PROMPT titles per workspace/environment"""
        # Create first PROMPT
        Artifact.objects.create(
            workspace=self.workspace,
            kind="PROMPT",
            environment="DEV",
            title="Duplicate Title",
            content="Content 1",
        )

        # Try to create duplicate PROMPT with same title in same workspace/environment
        # This should raise ValidationError because we override save() to call full_clean()
        with self.assertRaises(ValidationError) as context:
            Artifact.objects.create(
                workspace=self.workspace,
                kind="PROMPT",
                environment="DEV",
                title="Duplicate Title",
                content="Content 2",
            )

        # Check that the error message contains constraint information
        self.assertIn(
            "unique_title_per_workspace_environment_and_kind", str(context.exception)
        )

    def test_display_value_property(self):
        """Test display_value property for different artifact types"""
        # ENV_VAR display value
        env_var = Artifact.objects.create(
            workspace=self.workspace,
            kind="ENV_VAR",
            key="TEST_KEY",
            value="test_value",
            environment="DEV",
        )
        self.assertEqual(env_var.display_value, "test_value")

        # PROMPT display value (short content)
        short_prompt = Artifact.objects.create(
            workspace=self.workspace,
            kind="PROMPT",
            title="Short Prompt",
            content="Short content",
            environment="DEV",
        )
        self.assertEqual(short_prompt.display_value, "Short content")

        # PROMPT display value (long content)
        long_content = "x" * 150
        long_prompt = Artifact.objects.create(
            workspace=self.workspace,
            kind="PROMPT",
            title="Long Prompt",
            content=long_content,
            environment="DEV",
        )
        self.assertEqual(long_prompt.display_value, "x" * 100 + "...")

        # DOC_LINK display value
        doc_link = Artifact.objects.create(
            workspace=self.workspace,
            kind="DOC_LINK",
            title="Test Doc",
            url="https://example.com",
            environment="DEV",
        )
        self.assertEqual(doc_link.display_value, "https://example.com")

    def test_primary_identifier_property(self):
        """Test primary_identifier property for different artifact types"""
        # ENV_VAR primary identifier
        env_var = Artifact.objects.create(
            workspace=self.workspace,
            kind="ENV_VAR",
            key="TEST_KEY",
            value="test_value",
            environment="DEV",
        )
        self.assertEqual(env_var.primary_identifier, "TEST_KEY")

        # PROMPT primary identifier
        prompt = Artifact.objects.create(
            workspace=self.workspace,
            kind="PROMPT",
            title="Test Prompt",
            content="Content",
            environment="DEV",
        )
        self.assertEqual(prompt.primary_identifier, "Test Prompt")

        # DOC_LINK primary identifier
        doc_link = Artifact.objects.create(
            workspace=self.workspace,
            kind="DOC_LINK",
            title="Test Doc",
            url="https://example.com",
            environment="DEV",
        )
        self.assertEqual(doc_link.primary_identifier, "Test Doc")

    def test_default_environment_is_dev(self):
        """Test that default environment is DEV"""
        artifact = Artifact.objects.create(
            workspace=self.workspace,
            kind="ENV_VAR",
            key="TEST_KEY",
            value="test_value",
            # environment not specified
        )
        self.assertEqual(artifact.environment, "DEV")

    def test_metadata_field_functionality(self):
        """Test that metadata JSONField works correctly"""
        test_metadata = {
            "created_by": "test_user",
            "tags": ["important", "production"],
            "custom_field": "custom_value",
        }

        artifact = Artifact.objects.create(
            workspace=self.workspace,
            kind="ENV_VAR",
            key="METADATA_TEST",
            value="test_value",
            environment="DEV",
            metadata=test_metadata,
        )

        self.assertEqual(artifact.metadata, test_metadata)
        self.assertEqual(artifact.metadata["created_by"], "test_user")
        self.assertIn("important", artifact.metadata["tags"])

    def test_workspace_relationship(self):
        """Test workspace relationship and related_name"""
        # Create artifacts
        env_var = Artifact.objects.create(
            workspace=self.workspace,
            kind="ENV_VAR",
            key="TEST_KEY",
            value="test_value",
            environment="DEV",
        )

        prompt = Artifact.objects.create(
            workspace=self.workspace,
            kind="PROMPT",
            title="Test Prompt",
            content="Content",
            environment="DEV",
        )

        # Test related_name works
        artifacts = self.workspace.artifacts.all()  # type: ignore
        self.assertEqual(artifacts.count(), 2)
        self.assertIn(env_var, artifacts)
        self.assertIn(prompt, artifacts)

    def test_ordering_by_updated_at_desc(self):
        """Test that artifacts are ordered by updated_at descending"""
        # Create first artifact
        first_artifact = Artifact.objects.create(
            workspace=self.workspace,
            kind="ENV_VAR",
            key="FIRST_KEY",
            value="first_value",
            environment="DEV",
        )

        # Create second artifact (will have later timestamp)
        second_artifact = Artifact.objects.create(
            workspace=self.workspace,
            kind="ENV_VAR",
            key="SECOND_KEY",
            value="second_value",
            environment="DEV",
        )

        # Check ordering
        artifacts = Artifact.objects.all()
        self.assertEqual(artifacts[0], second_artifact)  # Most recent first
        self.assertEqual(artifacts[1], first_artifact)  # Older second


class TagModelTest(TestCase):
    """Tests for Tag model and Artifact ↔ Tag many-to-many through ArtifactTag."""

    def setUp(self):
        self.workspace = Workspace.objects.create(
            name="Tag Workspace",
            description="Workspace for tag tests",
            owner_uid="tag_user_1",
        )
        self.artifact = Artifact.objects.create(
            workspace=self.workspace,
            kind="ENV_VAR",
            environment="DEV",
            key="TAG_KEY",
            value="value",
        )

    def test_tag_creation(self):
        tag = Tag.objects.create(workspace=self.workspace, name="backend")
        self.assertEqual(tag.name, "backend")
        self.assertEqual(tag.workspace, self.workspace)

    def test_tag_uniqueness_per_workspace(self):
        from django.db import transaction
        Tag.objects.create(workspace=self.workspace, name="shared")
        # Wrap duplicate creation in an atomic block to avoid breaking the
        # outer TestCase transaction on SQLite
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Tag.objects.create(workspace=self.workspace, name="shared")
        # Same name in different workspace allowed
        ws2 = Workspace.objects.create(
            name="Second WS", description="Second", owner_uid="tag_user_2"
        )
        try:
            Tag.objects.create(workspace=ws2, name="shared")
        except IntegrityError:
            self.fail("Tag uniqueness wrongly enforced across workspaces")

    def test_assign_tag_to_artifact(self):
        tag = Tag.objects.create(workspace=self.workspace, name="api")
        self.artifact.tags.add(tag)
        self.artifact.refresh_from_db()
        self.assertIn(tag, self.artifact.tags.all())

    def test_artifact_tag_uniqueness(self):
        tag = Tag.objects.create(workspace=self.workspace, name="ops")
        ArtifactTag.objects.create(artifact=self.artifact, tag=tag)
        with self.assertRaises(IntegrityError):
            ArtifactTag.objects.create(artifact=self.artifact, tag=tag)

    def test_deleting_artifact_cascades_artifacttag_only(self):
        tag = Tag.objects.create(workspace=self.workspace, name="infra")
        self.artifact.tags.add(tag)
        self.assertEqual(ArtifactTag.objects.filter(tag=tag).count(), 1)
        self.artifact.delete()
        # Through row removed
        self.assertEqual(ArtifactTag.objects.filter(tag=tag).count(), 0)
        # Tag remains
        self.assertTrue(Tag.objects.filter(id=tag.id).exists())

    def test_deleting_tag_cascades_artifacttag_only(self):
        tag = Tag.objects.create(workspace=self.workspace, name="cli")
        self.artifact.tags.add(tag)
        self.assertEqual(ArtifactTag.objects.filter(artifact=self.artifact).count(), 1)
        tag.delete()
        # Through row removed
        self.assertEqual(ArtifactTag.objects.filter(artifact=self.artifact).count(), 0)
        # Artifact remains
        self.assertTrue(Artifact.objects.filter(id=self.artifact.id).exists())


class ArtifactViewSetTest(APITestCase):
    """Test Artifact ViewSet API endpoints with Firebase authentication and nested routing."""

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

        # Create test artifacts for testing
        self.create_test_artifacts()

    def create_test_artifacts(self):
        """Create sample artifacts for testing."""
        # ENV_VAR artifacts in different environments
        self.env_var_dev = Artifact.objects.create(
            workspace=self.user_workspace,
            kind="ENV_VAR",
            environment="DEV",
            key="API_KEY",
            value="dev_api_key_value",
            notes="Development API key",
        )

        self.env_var_prod = Artifact.objects.create(
            workspace=self.user_workspace,
            kind="ENV_VAR",
            environment="PROD",
            key="API_KEY",
            value="prod_api_key_value",
            notes="Production API key",
        )

        # PROMPT artifacts
        self.prompt_dev = Artifact.objects.create(
            workspace=self.user_workspace,
            kind="PROMPT",
            environment="DEV",
            title="Bug Report Template",
            content="Report bug: {{description}}\n\nSteps:\n{{steps}}",
            notes="Standard bug report format",
        )

        # DOC_LINK artifacts
        self.doc_link_dev = Artifact.objects.create(
            workspace=self.user_workspace,
            kind="DOC_LINK",
            environment="DEV",
            title="Django Documentation",
            url="https://docs.djangoproject.com",
            notes="Official Django docs",
        )

        # Artifact in other user's workspace
        self.other_artifact = Artifact.objects.create(
            workspace=self.other_workspace,
            kind="ENV_VAR",
            environment="DEV",
            key="OTHER_KEY",
            value="other_value",
        )

    def authenticate_user(self):
        """Helper method to authenticate user for tests."""
        self.client.credentials(HTTP_AUTHORIZATION="Bearer fake_token")

    def get_artifact_url(self, workspace_id=None, artifact_id=None):
        """Helper to build artifact URLs."""
        workspace_id = workspace_id or self.user_workspace.id
        base_url = f"/api/v1/workspaces/{workspace_id}/artifacts/"
        if artifact_id:
            return f"{base_url}{artifact_id}/"
        return base_url

    def test_list_artifacts_unauthenticated(self):
        """Test that unauthenticated requests are rejected."""
        response = self.client.get(self.get_artifact_url())
        # DRF returns 403 when no credentials are provided, 401 when invalid credentials are provided
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn(b"Authentication credentials were not provided", response.content)

    @patch("auth_firebase.authentication.firebase_auth.verify_id_token")
    def test_list_artifacts(self, mock_verify_token):
        """Test listing artifacts for a workspace."""
        mock_verify_token.return_value = {"uid": self.test_user_uid}
        self.authenticate_user()

        response = self.client.get(self.get_artifact_url())

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Response is paginated
        self.assertIn("results", response.data)
        artifacts = response.data["results"]
        self.assertEqual(len(artifacts), 4)  # 4 artifacts in user's workspace

        # Verify artifact data structure
        artifact_data = artifacts[0]
        self.assertIn("id", artifact_data)
        self.assertIn("kind", artifact_data)
        self.assertIn("environment", artifact_data)
        self.assertIn("workspace_name", artifact_data)

    @patch("auth_firebase.authentication.firebase_auth.verify_id_token")
    def test_create_env_var_artifact(self, mock_verify_token):
        """Test creating an ENV_VAR artifact."""
        mock_verify_token.return_value = {"uid": self.test_user_uid}
        self.authenticate_user()

        artifact_data = {
            "kind": "ENV_VAR",
            "environment": "STAGING",
            "key": "NEW_API_KEY",
            "value": "staging_api_key_value",
            "notes": "Staging environment API key",
        }

        response = self.client.post(self.get_artifact_url(), artifact_data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["kind"], "ENV_VAR")
        self.assertEqual(response.data["key"], "NEW_API_KEY")
        self.assertEqual(response.data["environment"], "STAGING")

        # Verify value is masked in response
        self.assertEqual(response.data["value"], "••••••")
        self.assertTrue(response.data["value_masked"])

        # Verify artifact was created in database
        artifact = Artifact.objects.get(id=response.data["id"])
        self.assertEqual(artifact.value, "staging_api_key_value")  # Real value in DB
