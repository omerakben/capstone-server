# DEADLINE Project Memory - Instructions & Project Details

## Project Overview

**DEADLINE** is a Django-based developer command center designed to unify the management of environment variables, prompts, and documentation links. This project addresses configuration fragmentation by providing a single, organized hub with environment-aware artifact management.

### Key Project Details

- **Framework**: Django 5.2 + Django REST Framework
- **Authentication**: Firebase Admin SDK with JWT tokens
- **Database**: SQLite for local development
- **Target Users**: Individual developers on local machines
- **Repository**: <https://github.com/omerakben/capstone-server>
- **Current Branch**: develop
- **Latest Commit**: Workspace Model Implementation (September 2, 2025)

## Technical Architecture

### Django Application Structure

```
deadline_api/          # Main Django project
├── workspaces/        # Workspace management app
├── artifacts/         # Artifact management app (polymorphic)
└── auth_firebase/     # Firebase authentication app
```

### Core Models (Planned)

1. **Workspace**: User-owned containers with Firebase UID ownership
2. **Artifact**: Polymorphic model with three types:
   - ENV_VAR: Environment variables (masked values)
   - PROMPT: Code/AI prompts (markdown, 10k char limit)
   - DOC_LINK: Documentation links with labels

### Authentication & Security

- Firebase UID-based row-level security
- Custom FirebaseAuthentication class extending BaseAuthentication
- IsOwner permission for object-level access control
- Masked sensitive values in API responses
- Mock authentication for local development

## Development Guidelines

### Copilot Instructions Location

- Primary: `.github/copilot-instructions.md`
- Specialized: `.github/deadline-co.md` (chat mode)
- Context: `.github/chatmodes/deadline-p.chatmode.md`

### Development Workflow

1. **Think-First Approach**: Always use sequential-thinking for complex decisions
2. **Type Safety**: Leverage Pylance for Python code intelligence
3. **Documentation**: Use Context7 for Django/DRF best practices
4. **Local Focus**: Optimize for SQLite and single-developer use

### Key Patterns

- Polymorphic model design for artifacts
- Dynamic serialization based on artifact type
- Environment-aware features (Dev/Staging/Prod as user categories)
- Cross-environment duplication capabilities
- Comprehensive validation with type-specific rules

## Implementation Status

### Completed Tasks

✅ **Django Project Setup (be-setup-task-001)**
- Django project initialization
- Three apps created: workspaces, artifacts, auth_firebase
- Settings configuration for local development
- Environment management with python-decouple
- CORS setup for localhost:3000
- API documentation with drf-spectacular
- Comprehensive .gitignore and README.md
- Initial commit pushed to develop branch

✅ **Firebase Authentication System (be-auth-task-001 & be-auth-task-002)**
- Firebase Admin SDK integration completed
- FirebaseAuthentication class extending BaseAuthentication
- Token verification with proper error handling
- Mock authentication for local development (test_user_uid_123)
- IsOwner permission class for row-level security
- Authentication endpoints: health, user_info, verify_token
- Django settings integration with REST_FRAMEWORK
- All endpoints tested and working correctly

✅ **Workspace Model Implementation (be-models-task-001)**

- Complete Workspace model with proper validation and constraints
- Firebase UID-based ownership with database indexing
- Unique constraint preventing duplicate names per user
- Comprehensive test suite with 15 passing test cases
- Django admin interface with proper fieldsets
- Migrations created and applied successfully

### Current Status: 7/14 tasks completed (50.0%)

### Next Phase

� **Model Implementation (be-models-task-001 & be-models-task-002)**
- Workspace model with Firebase UID ownership
- Polymorphic Artifact model with type-specific validation
- Database migrations and initial data setup

📋 **API Development (be-api-task-001)**
- Workspace ViewSet with ownership filtering
- Artifact ViewSet with nested routing
- Search and filtering capabilities

## Configuration Details

### Dependencies (requirements.txt)

- Django==5.2
- djangorestframework>=3.14
- django-cors-headers>=4.3.0
- python-decouple>=3.8
- firebase-admin>=6.4.0
- django-extensions>=3.2.0
- drf-spectacular>=0.26.0

### Environment Variables (.env.example)

- SECRET_KEY: Django secret key
- DEBUG: Enable/disable debug mode
- ALLOWED_HOSTS: Comma-separated allowed hosts
- FIREBASE_*: Firebase service account configuration
- USE_FIREBASE_MOCK: Enable mock auth for local dev

### Database Configuration

- SQLite database: `db.sqlite3` (ignored by git)
- Initial migrations applied
- Django admin enabled
- Debug toolbar configured for localhost

## API Design

### Planned Endpoints

```
/api/v1/workspaces/     # Workspace CRUD with ownership filtering
/api/v1/artifacts/      # Artifact CRUD with type-specific validation
/api/v1/auth/          # Firebase token verification and user info
/api/docs/             # Swagger UI documentation
/api/schema/           # OpenAPI schema
```

### Key Features

- Pagination: PageNumberPagination with 20 items per page
- Filtering: SearchFilter and OrderingFilter
- Authentication: Firebase JWT tokens (session auth for local dev)
- Permissions: IsAuthenticated + IsOwner for object-level security
- Documentation: Automated with drf-spectacular

## Security Considerations

### Data Protection

- Firebase UID-based access control
- Masked environment variable values in responses
- No sensitive data in version control
- Proper .gitignore for secrets and local files

### Authentication Flow

1. Frontend sends Firebase JWT token in Authorization header
2. FirebaseAuthentication class verifies token with Firebase Admin SDK
3. Extract Firebase UID and create user-like object
4. ViewSets filter data by owner_uid for row-level security

## Development Environment

### Local Setup

1. Python 3.12+ with virtual environment (.venv/)
2. Django development server on port 8000
3. Debug toolbar enabled for localhost
4. SQLite database in project root
5. CORS configured for localhost:3000 frontend

### Git Workflow

- Main branch: `main` (default)
- Development branch: `develop` (current)
- Feature branches: feature/* pattern recommended
- Conventional commits with clear scope and description

## Project Files Structure

### Documentation

- `README.md`: Project overview and setup instructions
- `my-docs/PRD.md`: Product requirements document
- `my-docs/server-TODO.md`: Implementation checklist
- `my-docs/*.png`: UI mockups and screenshots

### Configuration

- `deadline_api/settings.py`: Django configuration
- `deadline_api/urls.py`: URL routing
- `.env.example`: Environment template
- `.gitignore`: Comprehensive ignore rules

### Apps

- Each app has standard Django structure: models, views, urls, admin, tests
- URLs currently commented out until ViewSets are implemented
- Firebase authentication to be implemented in auth_firebase app

## Important Notes

### Environment Context

- "Dev/Staging/Production environments" refer to USER workspace features
- NOT deployment environments - always develop locally with SQLite
- Users categorize their workspaces with environment labels

### Performance Optimization

- select_related() and prefetch_related() for foreign keys
- Database indexes on owner_uid and workspace fields
- Pagination for all list endpoints
- SQLite optimization for local development

### Testing Strategy

- Mock Firebase authentication for unit tests
- Test artifact type-specific validation
- Test workspace ownership enforcement
- Integration tests for API endpoints

---

This memory document captures the current state and instructions for the DEADLINE project as of the initial setup completion.
