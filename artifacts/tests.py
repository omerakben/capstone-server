from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from artifacts.models import (
    Artifact,
    validate_env_var_key,
    validate_prompt_content_length,
)
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
