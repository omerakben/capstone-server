"""
Management command to seed demo data for demo@deadline.demo account.
Clears existing demo data and creates fresh sample workspaces with artifacts.

Usage: python manage.py seed_demo_data
"""

from django.core.management.base import BaseCommand

from artifacts.models import Artifact
from workspaces.models import Workspace


class Command(BaseCommand):
    help = "Seed demo data for demo@deadline.demo account (clears existing data)"

    def handle(self, *args, **options):
        # Demo user Firebase UID - should match Firebase Console
        # NOTE: Update this UID after creating demo@deadline.demo in Firebase
        DEMO_UID = "YVvUoxJZnmMSqYOthshayam8piD2"

        self.stdout.write("Clearing existing demo data...")
        Workspace.objects.filter(owner_uid=DEMO_UID).delete()

        self.stdout.write("Creating demo workspaces...")

        # ==============================================
        # Workspace 1: E-commerce Platform
        # ==============================================
        ws1 = Workspace.objects.create(
            name="E-commerce Platform",
            description="Production environment variables and documentation for online store",
            owner_uid=DEMO_UID,
        )

        # ENV_VAR artifacts for E-commerce
        Artifact.objects.create(
            workspace=ws1,
            kind="ENV_VAR",
            environment="PROD",
            key="DATABASE_URL",
            value="postgresql://user:password@prod-db.example.com:5432/ecommerce",
            notes="Production database connection",
        )
        Artifact.objects.create(
            workspace=ws1,
            kind="ENV_VAR",
            environment="PROD",
            key="STRIPE_SECRET_KEY",
            value="sk_test_DEMO_NOT_A_REAL_KEY_FOR_DEMONSTRATION_ONLY",
            notes="Stripe payment processing",
        )
        Artifact.objects.create(
            workspace=ws1,
            kind="ENV_VAR",
            environment="DEV",
            key="DATABASE_URL",
            value="postgresql://dev:devpass@localhost:5432/ecommerce_dev",
            notes="Development database",
        )

        # PROMPT artifacts for E-commerce
        Artifact.objects.create(
            workspace=ws1,
            kind="PROMPT",
            environment="DEV",
            title="Generate Checkout Flow",
            content="""Create a React checkout component with:
- Multi-step form (shipping, payment, review)
- Stripe integration
- Form validation with react-hook-form
- Loading states and error handling""",
            notes="Useful for building payment flows",
        )
        Artifact.objects.create(
            workspace=ws1,
            kind="PROMPT",
            environment="DEV",
            title="Create Django Product Model",
            content="""Generate a Django model for Product with:
- Name, description, price, SKU
- Category foreign key
- Image upload field
- Stock quantity
- Is active boolean
- Created/updated timestamps""",
            notes="Standard e-commerce product schema",
        )

        # DOC_LINK artifacts for E-commerce
        Artifact.objects.create(
            workspace=ws1,
            kind="DOC_LINK",
            environment="DEV",
            title="Stripe API Documentation",
            url="https://stripe.com/docs/api",
            notes="Payment gateway integration reference",
        )
        Artifact.objects.create(
            workspace=ws1,
            kind="DOC_LINK",
            environment="DEV",
            title="Next.js E-commerce Guide",
            url="https://nextjs.org/commerce",
            notes="Best practices for building e-commerce with Next.js",
        )

        # ==============================================
        # Workspace 2: Mobile App Backend
        # ==============================================
        ws2 = Workspace.objects.create(
            name="Mobile App Backend",
            description="API configurations, authentication setup, and deployment guides",
            owner_uid=DEMO_UID,
        )

        # ENV_VAR artifacts for Mobile Backend
        Artifact.objects.create(
            workspace=ws2,
            kind="ENV_VAR",
            environment="PROD",
            key="JWT_SECRET",
            value="super-secret-jwt-key-production-only-change-this",
            notes="JWT token signing key",
        )
        Artifact.objects.create(
            workspace=ws2,
            kind="ENV_VAR",
            environment="PROD",
            key="FIREBASE_CONFIG",
            value='{"apiKey":"AIzaSy...","authDomain":"app.firebaseapp.com","projectId":"app-prod"}',
            notes="Firebase configuration for mobile app",
        )

        # PROMPT artifacts for Mobile Backend
        Artifact.objects.create(
            workspace=ws2,
            kind="PROMPT",
            environment="DEV",
            title="Push Notification Handler",
            content="""Create an Express.js endpoint for push notifications:
- Accept FCM token and message payload
- Validate user permissions
- Send via Firebase Cloud Messaging
- Log delivery status
- Handle errors gracefully""",
            notes="Backend push notification implementation",
        )
        Artifact.objects.create(
            workspace=ws2,
            kind="PROMPT",
            environment="DEV",
            title="JWT Auth Middleware",
            content="""Create Node.js middleware for JWT authentication:
- Extract token from Authorization header
- Verify JWT signature
- Attach user info to request object
- Handle expired tokens
- Return 401 for invalid tokens""",
            notes="Standard authentication middleware pattern",
        )

        # DOC_LINK artifacts for Mobile Backend
        Artifact.objects.create(
            workspace=ws2,
            kind="DOC_LINK",
            environment="DEV",
            title="Firebase Cloud Messaging",
            url="https://firebase.google.com/docs/cloud-messaging",
            notes="Push notification setup and best practices",
        )
        Artifact.objects.create(
            workspace=ws2,
            kind="DOC_LINK",
            environment="DEV",
            title="Express.js Security Best Practices",
            url="https://expressjs.com/en/advanced/best-practice-security.html",
            notes="Production security checklist",
        )

        # Summary
        total_workspaces = Workspace.objects.filter(owner_uid=DEMO_UID).count()
        total_artifacts = Artifact.objects.filter(workspace__owner_uid=DEMO_UID).count()

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ Demo data seeded successfully!\n"
                f"   - Created {total_workspaces} workspaces\n"
                f"   - Created {total_artifacts} artifacts (ENV_VAR, PROMPT, DOC_LINK)\n"
                f"   - Ready for demo mode"
            )
        )
