# server/TODO.md

## Progress Summary

**Last Updated**: August 26, 2025
**Completion Status**: 4/14 main tasks completed (28.6%)
**Recent Completion**: Initial Django setup with proper structure ✅

### ✅ Completed Tasks

- `be-setup-task-001`: Django project initialization
- `be-setup-task-002`: DRF and CORS configuration
- `be-setup-task-003`: SQLite database setup
- `be-local-task-001`: Local development optimization

### 🔄 Next Priority

- `be-auth-task-001`: Firebase Authentication implementation
- `be-models-task-001`: Workspace model implementation
- `be-models-task-002`: Polymorphic Artifact model

## Scope & Assumptions

This backend implementation uses Django 5.2 with Django REST Framework to provide a RESTful API for the DEADLINE developer command center, with Firebase Authentication for token validation and SQLite as the database for local development. All API endpoints require Firebase auth except health checks, artifacts are polymorphic with type-specific validation, and workspace ownership is enforced at the ViewSet level using Firebase UID extraction from tokens. The application is designed for individual developer use on their local machine.

## Checklist

[x] be-setup-task-001 [plan] [M] — Initialize Django project with proper structure ✅ COMPLETED
   [x] be-setup-sub_task-001 — Create Django project named 'deadline_api' with django-admin
   [x] be-setup-sub_task-002 — Create apps: 'workspaces', 'artifacts', 'auth_firebase'
   [x] be-setup-sub_task-003 — Configure settings.py for local development environment
   [x] be-setup-sub_task-004 — Set up .env file handling with python-decouple for sensitive configs

[x] be-setup-task-002 [build] [S] — Configure Django REST Framework and CORS ✅ COMPLETED
   [x] be-setup-sub_task-001 — Install and configure djangorestframework in INSTALLED_APPS
   [x] be-setup-sub_task-002 — Set up django-cors-headers with localhost:3000 for local dev
   [x] be-setup-sub_task-003 — Configure DRF default authentication and permission classes
   [x] be-setup-sub_task-004 — Add pagination settings (PageNumberPagination, page_size=20)

[x] be-setup-task-003 [build] [S] — Set up SQLite database ✅ COMPLETED
   [x] be-setup-sub_task-001 — Configure SQLite database in settings.py for local storage
   [x] be-setup-sub_task-002 — Install and configure django-extensions for development helpers
   [x] be-setup-sub_task-003 — Run initial migrations and verify database schema
   [x] be-setup-sub_task-004 — Set up database file in project root with .gitignore entry

[ ] be-auth-task-001 [build] [L] — Implement Firebase Authentication middleware
   [x] be-auth-sub_task-001 — Install firebase-admin SDK and initialize with service account ✅ COMPLETED
   [ ] be-auth-sub_task-002 — Create FirebaseAuthentication class extending BaseAuthentication
   [ ] be-auth-sub_task-003 — Implement token verification in authenticate() method
   [ ] be-auth-sub_task-004 — Extract and return user UID from decoded token
   [ ] be-auth-sub_task-005 — Add proper error handling for expired/invalid tokens

[ ] be-auth-task-002 [build] [M] — Create permission classes
   [ ] be-auth-sub_task-001 — Build IsOwner permission class checking workspace.owner_uid
   [ ] be-auth-sub_task-002 — Create IsAuthenticated override using Firebase user
   [ ] be-auth-sub_task-003 — Add request.user injection with Firebase UID

[ ] be-models-task-001 [build] [M] — Implement Workspace model
   [ ] be-models-sub_task-001 — Define fields: id, name, description, owner_uid, created_at, updated_at
   [ ] be-models-sub_task-002 — Add index on owner_uid for query performance
   [ ] be-models-sub_task-003 — Implement **str** method and Meta ordering
   [ ] be-models-sub_task-004 — Add model validation for name length and characters

[ ] be-models-task-002 [build] [L] — Build polymorphic Artifact model
   [ ] be-models-sub_task-001 — Define base fields: id, workspace (FK), kind (choices), created_at, updated_at
   [ ] be-models-sub_task-002 — Add type-specific fields: key, value, title, content, url, metadata (JSONField)
   [ ] be-models-sub_task-003 — Implement clean() method for type-specific validation
   [ ] be-models-sub_task-004 — Add unique constraints for (workspace, kind, key) and (workspace, kind, title)
   [ ] be-models-sub_task-005 — Create indexes on kind and workspace fields

[ ] be-api-task-001 [build] [M] — Implement Workspace ViewSet
   [ ] be-api-sub_task-001 — Create WorkspaceSerializer with artifact count field
   [ ] be-api-sub_task-002 — Build ViewSet with list, create, retrieve, update, destroy actions
   [ ] be-api-sub_task-003 — Override get_queryset() to filter by request.user (owner_uid)
   [ ] be-api-sub_task-004 — Add prefetch_related for performance optimization with artifacts

[ ] be-api-task-002 [build] [L] — Create Artifact ViewSet with nested routing
   [ ] be-api-sub_task-001 — Build ArtifactSerializer with dynamic fields based on kind
   [ ] be-api-sub_task-002 — Implement nested routing under /workspaces/{id}/artifacts
   [ ] be-api-sub_task-003 — Add query parameter filtering by kind (ENV_VAR, PROMPT, DOC_LINK)
   [ ] be-api-sub_task-004 — Override create() to validate artifact type-specific fields
   [ ] be-api-sub_task-005 — Implement bulk operations for artifact management

[ ] be-api-task-003 [build] [M] — Add Docs Links API endpoints
   [ ] be-api-sub_task-001 — Create simplified DocLinkSerializer for DOC_LINK artifacts
   [ ] be-api-sub_task-002 — Build DocLinkViewSet filtering artifacts by kind=DOC_LINK
   [ ] be-api-sub_task-003 — Add URL validation in serializer
   [ ] be-api-sub_task-004 — Implement global docs endpoint aggregating across workspaces

[ ] be-api-task-004 [build] [M] — Implement Export/Import functionality
   [ ] be-api-sub_task-001 — Create export action on WorkspaceViewSet returning JSON
   [ ] be-api-sub_task-002 — Build import endpoint with JSON schema validation
   [ ] be-api-sub_task-003 — Add option to mask sensitive values in export
   [ ] be-api-sub_task-004 — Handle duplicate key conflicts on import with user choice

[ ] be-api-task-005 [build] [S] — Add search and filter capabilities
   [ ] be-api-sub_task-001 — Implement SearchFilter for artifact content and titles
   [ ] be-api-sub_task-002 — Add OrderingFilter for workspaces and artifacts
   [ ] be-api-sub_task-003 — Create text search across all artifact types

[ ] be-validation-task-001 [build] [M] — Implement business logic validations
   [ ] be-validation-sub_task-001 — Validate ENV_VAR key format (alphanumeric + underscore)
   [ ] be-validation-sub_task-002 — Ensure PROMPT content max length (10000 chars)
   [ ] be-validation-sub_task-003 — Validate DOC_LINK URLs with URLValidator
   [ ] be-validation-sub_task-004 — Prevent duplicate artifact keys within same workspace

[ ] be-validation-task-002 [build] [S] — Add request validation middleware
   [ ] be-validation-sub_task-001 — Create middleware for JSON payload size limits
   [ ] be-validation-sub_task-002 — Add basic rate limiting for API endpoints
   [ ] be-validation-sub_task-003 — Implement request logging for debugging

[ ] be-testing-task-001 [test] [L] — Write unit tests for models and serializers
   [ ] be-testing-sub_task-001 — Test Workspace model creation and validation
   [ ] be-testing-sub_task-002 — Test Artifact polymorphic behavior and constraints
   [ ] be-testing-sub_task-003 — Test serializer validation for each artifact type
   [ ] be-testing-sub_task-004 — Test unique constraints and cascade deletions

[ ] be-testing-task-002 [test] [L] — Create integration tests for API endpoints
   [ ] be-testing-sub_task-001 — Test authentication flow with mock Firebase tokens
   [ ] be-testing-sub_task-002 — Test CRUD operations for workspaces with permissions
   [ ] be-testing-sub_task-003 — Test artifact creation for each type
   [ ] be-testing-sub_task-004 — Test search and filter functionality
   [ ] be-testing-sub_task-005 — Test export/import functionality with edge cases

[x] be-local-task-001 [finish] [S] — Optimize for local development experience ✅ COMPLETED
   [ ] be-local-sub_task-001 — Create management commands for sample data generation
   [x] be-local-sub_task-002 — Add Django Debug Toolbar for development
   [x] be-local-sub_task-003 — Configure logging for console output in development
   [x] be-local-sub_task-004 — Create README with local setup instructions

[ ] be-local-task-002 [finish] [S] — Add development utilities
   [ ] be-local-sub_task-001 — Create health check endpoint at /api/health
   [ ] be-local-sub_task-002 — Add database backup/restore utilities for local SQLite
   [ ] be-local-sub_task-003 — Implement data reset command for testing
   [x] be-local-sub_task-004 — Add API documentation with drf-spectacular ✅ COMPLETED

## Open Questions / Risks

- Firebase Admin SDK initialization overhead for local development
- SQLite file management and backup strategy for local data
- Polymorphic artifact model complexity vs separate models trade-off
- JSON field query performance in SQLite
- Token verification caching strategy for local performance
- Data migration strategy if user wants to move to cloud later
- Local storage limits for artifacts and metadata
- Handling of secrets in local SQLite database
- Cross-platform compatibility (Windows/Mac/Linux) for local setup

## References

- <https://www.django-rest-framework.org/>
- <https://firebase.google.com/docs/admin/setup>
- <https://docs.djangoproject.com/en/5.2/>
- <https://github.com/encode/django-cors-headers>
