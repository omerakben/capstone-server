"""
Management command to populate demo workspace with sample artifacts.

Usage: python manage.py populate_demo_workspace
"""

from django.core.management.base import BaseCommand

from artifacts.models import Artifact, Tag
from workspaces.models import EnvironmentType, Workspace, WorkspaceEnvironment


class Command(BaseCommand):
    help = "Populate demo workspace with sample artifacts for demonstration"

    def handle(self, *args, **options):
        demo_uid = "demo_user_deadline_2025"

        # Check if demo workspace already has artifacts
        try:
            workspace = Workspace.objects.get(owner_uid=demo_uid, name="Demo Workspace")
            if workspace.artifacts.exists():
                self.stdout.write(
                    self.style.WARNING(
                        "Demo workspace already has artifacts. Skipping population."
                    )
                )
                return
        except Workspace.DoesNotExist:
            # Create demo workspace
            workspace = Workspace.objects.create(
                owner_uid=demo_uid,
                name="Demo Workspace",
                description="Demo workspace for exploring DEADLINE features",
            )
            self.stdout.write(
                self.style.SUCCESS(f"Created demo workspace: {workspace.name}")
            )

        # Get existing environment types (created by migration)
        env_types = {}
        for slug in ["DEV", "STAGING", "PROD"]:
            try:
                env_type = EnvironmentType.objects.get(slug=slug)
                env_types[slug] = env_type
            except EnvironmentType.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(
                        f"Environment type {slug} not found. Run migrations first."
                    )
                )
                return

        # Create workspace environments
        for env_type in env_types.values():
            WorkspaceEnvironment.objects.get_or_create(
                workspace=workspace, environment_type=env_type
            )

        # Create tags
        tag_names = [
            "demo",
            "production",
            "backend",
            "frontend",
            "ai",
            "development",
            "payments",
            "security",
            "customer-service",
            "reference",
        ]
        tags = {}
        for tag_name in tag_names:
            tag, created = Tag.objects.get_or_create(
                workspace=workspace, name=tag_name
            )
            tags[tag_name] = tag
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created tag: {tag_name}"))

        # Create ENV_VAR artifacts
        env_vars = [
            {
                "key": "DATABASE_URL",
                "value": "postgresql://user:password@host:5432/database",
                "environment": "PROD",
                "notes": "Production database connection string",
                "tags": ["production", "backend"],
            },
            {
                "key": "STRIPE_API_KEY",
                "value": "sk_test_DEMO_NOT_REAL",
                "environment": "PROD",
                "notes": "Stripe payment processing key",
                "tags": ["production", "payments"],
            },
            {
                "key": "JWT_SECRET",
                "value": "super_secret_key_do_not_share_12345",
                "environment": "PROD",
                "notes": "JWT signing secret for authentication tokens",
                "tags": ["production", "security"],
            },
        ]

        for env_var in env_vars:
            artifact = Artifact.objects.create(
                workspace=workspace,
                kind="ENV_VAR",
                key=env_var["key"],
                value=env_var["value"],
                environment=env_var["environment"],
                notes=env_var["notes"],
            )
            # Add tags
            for tag_name in env_var["tags"]:
                artifact.tags.add(tags[tag_name])

            self.stdout.write(
                self.style.SUCCESS(f"Created ENV_VAR: {env_var['key']}")
            )

        # Create PROMPT artifacts
        prompts = [
            {
                "title": "Code Review Agent",
                "content": """You are a senior code reviewer with expertise in software engineering best practices.

Your responsibilities:
1. **Security Analysis**: Identify potential security vulnerabilities (SQL injection, XSS, CSRF, etc.)
2. **Performance Review**: Spot inefficient algorithms, N+1 queries, and memory leaks
3. **Best Practices**: Ensure code follows SOLID principles, DRY, and language-specific conventions
4. **Testing Coverage**: Verify unit tests cover edge cases and error handling
5. **Documentation**: Check for clear comments, docstrings, and README updates

Always provide:
- Specific line numbers for issues
- Concrete examples of improvements
- Rationale for each recommendation

Be constructive and educational in your feedback.""",
                "environment": "DEV",
                "notes": "AI prompt for automated code review in CI/CD pipeline",
                "tags": ["ai", "development"],
            },
            {
                "title": "Customer Support Bot",
                "content": """You are a friendly and helpful customer support agent for an e-commerce platform.

Guidelines:
- **Tone**: Always be polite, empathetic, and professional
- **Process**: Ask clarifying questions before providing solutions
- **Solutions**: Provide step-by-step instructions with screenshots when possible
- **Escalation**: Know when to escalate to human support (refunds, account security issues)

Common scenarios:
1. Order tracking: Guide users to tracking page with order number
2. Returns/exchanges: Explain 30-day return policy and process
3. Payment issues: Verify order status and payment confirmation
4. Account access: Help with password reset (never ask for passwords)

Remember: Customer satisfaction is our top priority!""",
                "environment": "PROD",
                "notes": "Customer support chatbot prompt for Zendesk integration",
                "tags": ["ai", "customer-service", "production"],
            },
        ]

        for prompt in prompts:
            artifact = Artifact.objects.create(
                workspace=workspace,
                kind="PROMPT",
                title=prompt["title"],
                content=prompt["content"],
                environment=prompt["environment"],
                notes=prompt["notes"],
            )
            # Add tags
            for tag_name in prompt["tags"]:
                artifact.tags.add(tags[tag_name])

            self.stdout.write(self.style.SUCCESS(f"Created PROMPT: {prompt['title']}"))

        # Create DOC_LINK artifacts
        doc_links = [
            {
                "title": "Django REST Framework - Serializers",
                "url": "https://www.django-rest-framework.org/api-guide/serializers/",
                "environment": "DEV",
                "notes": "Official DRF documentation for building REST APIs",
                "tags": ["backend", "reference", "development"],
            },
        ]

        for doc_link in doc_links:
            artifact = Artifact.objects.create(
                workspace=workspace,
                kind="DOC_LINK",
                title=doc_link["title"],
                url=doc_link["url"],
                environment=doc_link["environment"],
                notes=doc_link["notes"],
            )
            # Add tags
            for tag_name in doc_link["tags"]:
                artifact.tags.add(tags[tag_name])

            self.stdout.write(
                self.style.SUCCESS(f"Created DOC_LINK: {doc_link['title']}")
            )

        # Summary
        artifact_count = workspace.artifacts.count()
        tag_count = workspace.tags.count()

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ Demo workspace populated successfully!"
            )
        )
        self.stdout.write(f"   - {artifact_count} artifacts created")
        self.stdout.write(f"   - {tag_count} tags created")
        self.stdout.write(f"   - Workspace: {workspace.name} (UID: {demo_uid})")
