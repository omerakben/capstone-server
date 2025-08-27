---
applyTo: "**"
---

# DEADLINE - Developer Command Center

## Django Backend Copilot Instructions

<!--
This file contains comprehensive instructions for developing the DEADLINE project,
a Django-based developer command center for managing environment variables, prompts, and documentation links.
-->

## Project Overview

**DEADLINE** is a web-based command center that consolidates critical developer workflow elements into a single, organized hub. It addresses configuration fragmentation by providing a unified platform with environment-aware artifact management, reducing context switching and preventing misconfiguration.

### Key Value Propositions

- **Unified Hub**: Single source of truth for environment configs, prompts, and documentation
- **Environment Awareness**: First-class support for Dev/Staging/Production separation (user feature)
- **Security First**: Masked secrets, Firebase authentication, and safe export/import
- **Developer Focused**: Built by developers, for developers' actual workflow needs

### Important Clarification

**Development/Staging/Production environments** in this context refer to **user workspace features**, NOT our local development environment. Users create workspaces and assign them environment categories (Dev/Staging/Prod) to organize their artifacts. We are always developing locally using SQLite.

---

## 📋 TODO Management & Workflow Rules

### 🔄 TODO Completion Protocol

**MANDATORY WORKFLOW** when completing any task from `my-docs/server-TODO.md`:

#### 1. **Update TODO Status**

```markdown
# Before

[ ] be-setup-task-001 [plan] [M] — Initialize Django project with proper structure

# After

[x] be-setup-task-001 [plan] [M] — Initialize Django project with proper structure ✅ COMPLETED
```

#### 2. **Update Progress Summary**

Update the progress summary section in `server-TODO.md`:

```markdown
## Progress Summary

**Last Updated**: [Current Date]
**Completion Status**: X/14 main tasks completed (XX.X%)
**Recent Completion**: [Task description] ✅
```

#### 3. **Memory Documentation**

Use `#memory` tools to add observations:

- Task completion details
- Implementation patterns discovered
- Lessons learned
- Architecture decisions made

#### 4. **Pre-Push Quality Checks**

**NEVER PUSH** without completing ALL of these:

✅ **No Lint Warnings**:

```bash
# Check for Python linting issues
pylint deadline_api/ workspaces/ artifacts/ auth_firebase/
# Fix all warnings and errors
```

✅ **No Type Errors**:

```bash
# Run type checking with Pylance/mypy
mypy deadline_api/ --ignore-missing-imports
```

✅ **Django Checks Pass**:

```bash
python manage.py check --deploy
# Resolve all issues before pushing
```

✅ **Tests Pass**:

```bash
python manage.py test
# All tests must pass
```

✅ **Migrations Clean**:

```bash
python manage.py makemigrations --check --dry-run
# No pending migrations
```

✅ **Import Organization**:

```bash
# Use isort for import sorting
isort . --check-only --diff
```

#### 5. **Commit Message Format**

Use conventional commits with task reference:

```bash
git commit -m "feat: Complete be-auth-task-001 Firebase authentication

✅ Implemented FirebaseAuthentication class with token verification
✅ Added IsOwner permission for row-level security
✅ Created mock authentication for local development
✅ Added comprehensive error handling and logging

Closes: be-auth-task-001
Tests: All authentication tests passing
Lint: No warnings or errors"
```

### 🧠 Memory Management Rules

#### When to Add Memory

- **Task Completion**: Document what was implemented and how
- **Architecture Decisions**: Record why specific patterns were chosen
- **Problem Solutions**: Capture debugging insights and solutions
- **Pattern Discovery**: Note reusable patterns for future tasks

#### Memory Categories

```python
# Use these entity types consistently
"task_completion"     # Completed TODO tasks
"implementation_pattern"  # Reusable code patterns
"architecture_decision"   # Design choices made
"debugging_solution"      # Problem resolution steps
"performance_optimization" # Speed/efficiency improvements
```

#### Memory Example

```python
mcp_memory_create_entities([{
    "entityType": "task_completion",
    "name": "be-auth-task-001",
    "observations": [
        "Firebase Admin SDK integration completed successfully",
        "Custom FirebaseAuthentication class extends BaseAuthentication",
        "Mock authentication implemented for local development",
        "Row-level security with IsOwner permission class",
        "Comprehensive error handling for token verification failures"
    ]
}])
```

### 🚫 Pre-Push Blockers

**DO NOT PUSH** if any of these exist:

❌ **Pylance/Linting Errors**: Red squiggly lines in VS Code
❌ **Django Check Failures**: `python manage.py check` reports issues
❌ **Test Failures**: Any unit or integration test fails
❌ **Import Errors**: Unresolved import statements
❌ **Type Errors**: Incorrect type annotations
❌ **TODO Inconsistency**: server-TODO.md not updated for completed work
❌ **Missing Memory**: No memory documentation for significant work

### 📊 Quality Metrics Tracking

Track these metrics for each push:

- **Test Coverage**: Maintain >80% coverage
- **Lint Score**: 9.0+ pylint score required
- **Type Coverage**: 100% for new code
- **Documentation**: All public methods documented
- **Performance**: No N+1 queries in Django ORM

---

## Technology Stack

### Backend Framework

- **Django 5.2**: Latest LTS with modern features
- **Django REST Framework**: RESTful API development
- **SQLite**: Local development database (NOT PostgreSQL)
- **Firebase Admin SDK**: Authentication and user management
- **python-decouple**: Environment variable management

### Key Dependencies

```python
# Core Framework
Django==5.2
djangorestframework>=3.14
django-cors-headers
python-decouple

# Authentication
firebase-admin

# Development
django-extensions
django-debug-toolbar
drf-spectacular  # API documentation
```

### Project Structure

```
deadline_api/
├── manage.py
├── deadline_api/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── workspaces/          # Workspace management app
├── artifacts/           # Artifact management app
├── auth_firebase/       # Firebase authentication app
├── db.sqlite3          # Local SQLite database
└── requirements.txt
```

---

## Architecture Patterns

### Django Apps Organization

#### 1. `workspaces` App

```python
# models.py
class Workspace(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    owner_uid = models.CharField(max_length=128, db_index=True)  # Firebase UID
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['owner_uid']),
        ]

    def __str__(self):
        return f"{self.name} ({self.owner_uid})"
```

#### 2. `artifacts` App - Polymorphic Model Design

```python
# models.py
class Artifact(models.Model):
    ARTIFACT_KINDS = [
        ('ENV_VAR', 'Environment Variable'),
        ('PROMPT', 'Code/AI Prompt'),
        ('DOC_LINK', 'Documentation Link'),
    ]

    id = models.AutoField(primary_key=True)
    workspace = models.ForeignKey('workspaces.Workspace', on_delete=models.CASCADE, related_name='artifacts')
    kind = models.CharField(max_length=20, choices=ARTIFACT_KINDS, db_index=True)

    # Common fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)

    # Type-specific fields (polymorphic design)
    # ENV_VAR fields
    key = models.CharField(max_length=255, blank=True)  # For ENV_VAR
    value = models.TextField(blank=True)  # For ENV_VAR

    # PROMPT fields
    title = models.CharField(max_length=255, blank=True)  # For PROMPT, DOC_LINK
    content = models.TextField(blank=True)  # For PROMPT (markdown)

    # DOC_LINK fields
    url = models.URLField(blank=True)  # For DOC_LINK
    label = models.CharField(max_length=255, blank=True)  # For DOC_LINK

    # Metadata storage for additional fields
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['workspace', 'kind']),
            models.Index(fields=['kind']),
        ]
        constraints = [
            # Unique constraints for different artifact types
            models.UniqueConstraint(
                fields=['workspace', 'kind', 'key'],
                condition=models.Q(kind='ENV_VAR') & ~models.Q(key=''),
                name='unique_env_var_key_per_workspace'
            ),
            models.UniqueConstraint(
                fields=['workspace', 'kind', 'title'],
                condition=models.Q(kind__in=['PROMPT', 'DOC_LINK']) & ~models.Q(title=''),
                name='unique_title_per_workspace_and_kind'
            ),
        ]

    def clean(self):
        """Type-specific validation"""
        if self.kind == 'ENV_VAR':
            if not self.key:
                raise ValidationError('ENV_VAR requires a key')
            if not re.match(r'^[A-Z0-9_]+$', self.key):
                raise ValidationError('ENV_VAR key must be alphanumeric with underscores')
        elif self.kind == 'PROMPT':
            if not self.title:
                raise ValidationError('PROMPT requires a title')
            if len(self.content) > 10000:
                raise ValidationError('PROMPT content cannot exceed 10,000 characters')
        elif self.kind == 'DOC_LINK':
            if not self.title or not self.url:
                raise ValidationError('DOC_LINK requires both title and URL')
```

#### 3. `auth_firebase` App

```python
# authentication.py
from firebase_admin import auth as firebase_auth
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

class FirebaseAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None

        token = auth_header.split(' ')[1]
        try:
            decoded_token = firebase_auth.verify_id_token(token)
            uid = decoded_token['uid']

            # Create a user-like object with Firebase UID
            user = type('FirebaseUser', (), {
                'uid': uid,
                'is_authenticated': True,
                'is_anonymous': False,
            })()

            return (user, token)
        except Exception as e:
            raise AuthenticationFailed(f'Invalid token: {str(e)}')

# permissions.py
from rest_framework.permissions import BasePermission

class IsOwner(BasePermission):
    """Object-level permission to only allow owners of a workspace to access it."""

    def has_object_permission(self, request, view, obj):
        # Assumes obj has owner_uid field (workspace or related model)
        if hasattr(obj, 'owner_uid'):
            return obj.owner_uid == request.user.uid
        elif hasattr(obj, 'workspace'):
            return obj.workspace.owner_uid == request.user.uid
        return False
```

---

## Business Logic Implementation

### Artifact Type Validation

#### ENV_VAR Validation

```python
# artifacts/validators.py
import re
from django.core.exceptions import ValidationError

def validate_env_var_key(value):
    """Validate ENV_VAR keys are alphanumeric with underscores"""
    if not re.match(r'^[A-Z0-9_]+$', value):
        raise ValidationError('ENV_VAR key must be uppercase alphanumeric with underscores')

def validate_prompt_content_length(value):
    """Validate PROMPT content doesn't exceed 10,000 characters"""
    if len(value) > 10000:
        raise ValidationError('PROMPT content cannot exceed 10,000 characters')
```

### Environment-Aware Features

```python
# The "environments" (Dev/Staging/Prod) are USER features, not deployment environments
# Users assign these categories to organize their artifacts within workspaces

# artifacts/models.py - Extended for environment awareness
class Artifact(models.Model):
    # ... existing fields ...
    environment = models.CharField(
        max_length=20,
        choices=[
            ('DEV', 'Development'),
            ('STAGING', 'Staging'),
            ('PROD', 'Production'),
        ],
        default='DEV'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['workspace', 'kind', 'key', 'environment'],
                condition=models.Q(kind='ENV_VAR') & ~models.Q(key=''),
                name='unique_env_var_key_per_workspace_environment'
            ),
        ]
```

### Cross-Environment Duplication

```python
# artifacts/views.py
from rest_framework.decorators import action
from rest_framework.response import Response

class ArtifactViewSet(viewsets.ModelViewSet):
    @action(detail=True, methods=['post'])
    def duplicate_to_environment(self, request, pk=None):
        """Duplicate artifact to a different environment"""
        artifact = self.get_object()
        target_environment = request.data.get('environment')

        if target_environment not in ['DEV', 'STAGING', 'PROD']:
            return Response({'error': 'Invalid environment'}, status=400)

        # Create duplicate with new environment
        duplicate_data = {
            'workspace': artifact.workspace.id,
            'kind': artifact.kind,
            'environment': target_environment,
            'key': artifact.key,
            'value': artifact.value,
            'title': artifact.title,
            'content': artifact.content,
            'url': artifact.url,
            'label': artifact.label,
            'notes': artifact.notes,
        }

        serializer = self.get_serializer(data=duplicate_data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)
```

---

## API Design Patterns

### ViewSet Implementation

```python
# workspaces/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count

class WorkspaceViewSet(viewsets.ModelViewSet):
    serializer_class = WorkspaceSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        """Filter workspaces by authenticated user"""
        return Workspace.objects.filter(
            owner_uid=self.request.user.uid
        ).prefetch_related('artifacts')

    def perform_create(self, serializer):
        """Automatically set owner_uid on creation"""
        serializer.save(owner_uid=self.request.user.uid)

    @action(detail=True, methods=['post'])
    def export(self, request, pk=None):
        """Export workspace to JSON"""
        workspace = self.get_object()
        mask_secrets = request.data.get('mask_secrets', True)

        export_data = {
            'workspace': WorkspaceSerializer(workspace).data,
            'artifacts': []
        }

        for artifact in workspace.artifacts.all():
            artifact_data = ArtifactSerializer(artifact).data

            # Mask sensitive values if requested
            if mask_secrets and artifact.kind == 'ENV_VAR':
                artifact_data['value'] = '••••••'

            export_data['artifacts'].append(artifact_data)

        return Response(export_data)

    @action(detail=False, methods=['post'])
    def import_data(self, request):
        """Import workspace from JSON"""
        # Implementation for importing JSON data with conflict resolution
        pass
```

### Serializer Patterns

```python
# artifacts/serializers.py
class ArtifactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Artifact
        fields = '__all__'

    def to_representation(self, instance):
        """Dynamic serialization based on artifact kind"""
        data = super().to_representation(instance)

        if instance.kind == 'ENV_VAR':
            # Remove unused fields for ENV_VAR
            data.pop('title', None)
            data.pop('content', None)
            data.pop('url', None)
            data.pop('label', None)
        elif instance.kind == 'PROMPT':
            # Remove unused fields for PROMPT
            data.pop('key', None)
            data.pop('value', None)
            data.pop('url', None)
            data.pop('label', None)
        elif instance.kind == 'DOC_LINK':
            # Remove unused fields for DOC_LINK
            data.pop('key', None)
            data.pop('value', None)
            data.pop('content', None)

        return data

    def validate(self, attrs):
        """Type-specific validation"""
        kind = attrs.get('kind')

        if kind == 'ENV_VAR':
            if not attrs.get('key'):
                raise serializers.ValidationError('ENV_VAR requires a key')

        elif kind == 'PROMPT':
            if not attrs.get('title'):
                raise serializers.ValidationError('PROMPT requires a title')

        elif kind == 'DOC_LINK':
            if not attrs.get('title') or not attrs.get('url'):
                raise serializers.ValidationError('DOC_LINK requires title and URL')

        return attrs

# Global docs serializer for simplified DOC_LINK representation
class DocLinkSerializer(serializers.ModelSerializer):
    workspace_name = serializers.CharField(source='workspace.name', read_only=True)

    class Meta:
        model = Artifact
        fields = ['id', 'title', 'url', 'label', 'notes', 'workspace_name', 'created_at']
```

### Nested Routing

```python
# urls.py
from rest_framework_nested import routers

router = routers.DefaultRouter()
router.register(r'workspaces', WorkspaceViewSet, basename='workspace')

workspaces_router = routers.NestedDefaultRouter(router, r'workspaces', lookup='workspace')
workspaces_router.register(r'artifacts', ArtifactViewSet, basename='workspace-artifacts')

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/', include(workspaces_router.urls)),
    path('api/docs/', include('artifacts.urls')),  # Global docs endpoint
    path('api/health/', health_check),
]
```

---

## Security & Authentication

### Firebase Integration

```python
# settings.py
import firebase_admin
from firebase_admin import credentials

# Initialize Firebase Admin SDK
if not firebase_admin._apps:
    cred = credentials.Certificate('path/to/serviceAccountKey.json')
    firebase_admin.initialize_app(cred)

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'auth_firebase.authentication.FirebaseAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
}
```

### Data Security Patterns

```python
# Masked value display in serializers
class SecureValueField(serializers.Field):
    """Field that masks sensitive values in read operations"""

    def to_representation(self, value):
        if value:
            return '••••••'  # Always mask in API responses
        return value

    def to_internal_value(self, data):
        return data  # Accept actual value for writes

# Usage in ENV_VAR serialization
class EnvVarSerializer(serializers.ModelSerializer):
    value = SecureValueField()

    class Meta:
        model = Artifact
        fields = ['id', 'key', 'value', 'notes']
```

### Permission Implementation

```python
# Permission matrix for different operations
class WorkspacePermission(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # All operations require ownership
        return obj.owner_uid == request.user.uid

class ArtifactPermission(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Access through workspace ownership
        return obj.workspace.owner_uid == request.user.uid
```

---

## Search & Filtering

### Global Search Implementation

```python
# artifacts/views.py
from django.db.models import Q
from rest_framework.filters import SearchFilter, OrderingFilter

class ArtifactViewSet(viewsets.ModelViewSet):
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['key', 'title', 'content', 'notes', 'url']
    ordering_fields = ['created_at', 'updated_at', 'kind']
    ordering = ['-updated_at']

    def get_queryset(self):
        queryset = Artifact.objects.filter(
            workspace__owner_uid=self.request.user.uid
        )

        # Filter by kind
        kind = self.request.query_params.get('kind')
        if kind:
            queryset = queryset.filter(kind=kind)

        # Filter by environment
        environment = self.request.query_params.get('environment')
        if environment:
            queryset = queryset.filter(environment=environment)

        return queryset.select_related('workspace')

# Global search endpoint
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def global_search(request):
    """Search across all user's artifacts"""
    query = request.query_params.get('q', '')
    if not query:
        return Response({'results': []})

    artifacts = Artifact.objects.filter(
        workspace__owner_uid=request.user.uid
    ).filter(
        Q(key__icontains=query) |
        Q(title__icontains=query) |
        Q(content__icontains=query) |
        Q(notes__icontains=query) |
        Q(url__icontains=query)
    ).select_related('workspace')[:50]

    serializer = ArtifactSerializer(artifacts, many=True)
    return Response({'results': serializer.data})
```

---

## Performance Optimization

### Database Query Optimization

```python
# Efficient queryset patterns
class WorkspaceViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return Workspace.objects.filter(
            owner_uid=self.request.user.uid
        ).prefetch_related(
            'artifacts'  # Avoid N+1 queries
        ).annotate(
            artifact_count=Count('artifacts')
        )

# Index definitions for optimal performance
class Workspace(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['owner_uid']),
            models.Index(fields=['owner_uid', '-updated_at']),
        ]

class Artifact(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['workspace', 'kind']),
            models.Index(fields=['workspace', 'environment']),
            models.Index(fields=['kind', '-updated_at']),
        ]
```

### Pagination and Caching

```python
# settings.py - Pagination configuration
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
}

# Custom pagination for large datasets
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 100
```

---

## Local Development

### Environment Setup

```python
# settings.py - Local development configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# CORS configuration for frontend (localhost:3000)
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Debug toolbar for development
if DEBUG:
    INSTALLED_APPS.append('debug_toolbar')
    MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
    INTERNAL_IPS = ['127.0.0.1']
```

### Management Commands

```python
# workspaces/management/commands/create_sample_data.py
from django.core.management.base import BaseCommand
from workspaces.models import Workspace
from artifacts.models import Artifact

class Command(BaseCommand):
    help = 'Create sample data for development'

    def add_arguments(self, parser):
        parser.add_argument('--user-uid', type=str, required=True)

    def handle(self, *args, **options):
        user_uid = options['user_uid']

        # Create sample workspace
        workspace = Workspace.objects.create(
            name='Sample Project',
            description='A sample workspace for development',
            owner_uid=user_uid
        )

        # Create sample artifacts
        Artifact.objects.create(
            workspace=workspace,
            kind='ENV_VAR',
            key='API_KEY',
            value='sample_api_key_value',
            environment='DEV'
        )

        Artifact.objects.create(
            workspace=workspace,
            kind='PROMPT',
            title='Bug Report Template',
            content='## Bug Report\n\n**Description:**\n{{description}}\n\n**Steps:**\n{{steps}}',
            environment='DEV'
        )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created sample data for user {user_uid}')
        )
```

### Health Check Endpoint

```python
# artifacts/views.py
from django.http import JsonResponse
from django.db import connection

def health_check(request):
    """Health check endpoint for monitoring"""
    try:
        # Test database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")

        return JsonResponse({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': timezone.now().isoformat()
        })
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=500)
```

---

## Testing Strategy

### Model Tests

```python
# tests/test_models.py
from django.test import TestCase
from django.core.exceptions import ValidationError
from workspaces.models import Workspace
from artifacts.models import Artifact

class ArtifactModelTest(TestCase):
    def setUp(self):
        self.workspace = Workspace.objects.create(
            name='Test Workspace',
            owner_uid='test_user_uid'
        )

    def test_env_var_validation(self):
        """Test ENV_VAR key validation"""
        artifact = Artifact(
            workspace=self.workspace,
            kind='ENV_VAR',
            key='invalid-key',  # Invalid characters
            value='test_value'
        )

        with self.assertRaises(ValidationError):
            artifact.full_clean()

    def test_unique_constraints(self):
        """Test unique constraints for artifact keys"""
        Artifact.objects.create(
            workspace=self.workspace,
            kind='ENV_VAR',
            key='DUPLICATE_KEY',
            value='value1',
            environment='DEV'
        )

        # Should raise IntegrityError for duplicate key in same workspace/environment
        with self.assertRaises(IntegrityError):
            Artifact.objects.create(
                workspace=self.workspace,
                kind='ENV_VAR',
                key='DUPLICATE_KEY',
                value='value2',
                environment='DEV'
            )
```

### API Tests with Mock Firebase

```python
# tests/test_api.py
from unittest.mock import patch, MagicMock
from rest_framework.test import APITestCase
from rest_framework import status

class WorkspaceAPITest(APITestCase):
    def setUp(self):
        self.mock_user = MagicMock()
        self.mock_user.uid = 'test_user_uid'
        self.mock_user.is_authenticated = True

    @patch('auth_firebase.authentication.firebase_auth.verify_id_token')
    def test_create_workspace(self, mock_verify_token):
        """Test workspace creation with Firebase auth"""
        mock_verify_token.return_value = {'uid': 'test_user_uid'}

        self.client.credentials(HTTP_AUTHORIZATION='Bearer fake_token')

        response = self.client.post('/api/workspaces/', {
            'name': 'Test Workspace',
            'description': 'A test workspace'
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Test Workspace')
        self.assertEqual(response.data['owner_uid'], 'test_user_uid')
```

---

## Development Best Practices

### Code Organization

```python
# Use consistent import ordering
# Standard library imports
import re
from typing import Dict, List, Optional

# Django imports
from django.db import models
from django.core.exceptions import ValidationError

# Third-party imports
from rest_framework import serializers, viewsets
from rest_framework.decorators import action

# Local imports
from .models import Workspace, Artifact
from .permissions import IsOwner
```

### Error Handling

```python
# Consistent error response format
from rest_framework.views import exception_handler
from rest_framework.response import Response

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        custom_response_data = {
            'error': {
                'status_code': response.status_code,
                'message': response.data.get('detail', 'An error occurred'),
                'timestamp': timezone.now().isoformat()
            }
        }
        response.data = custom_response_data

    return response
```

### Logging Configuration

```python
# settings.py - Logging for development
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'deadline_api': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

---

## Key Implementation Guidelines

### 1. Always Use Firebase Authentication

- All API endpoints except `/api/health/` require Firebase authentication
- Extract `uid` from Firebase token and use for row-level security
- Never trust client-provided user IDs

### 2. Polymorphic Model Best Practices

- Use the single `Artifact` model with `kind` field for all artifact types
- Implement type-specific validation in `clean()` method
- Use dynamic serialization based on `kind`

### 3. Environment Handling

- Remember: Dev/Staging/Prod are USER workspace features, not deployment environments
- Always develop locally with SQLite
- Support cross-environment duplication of artifacts

### 4. Security Priorities

- Mask sensitive values (ENV_VAR) in API responses
- Implement proper row-level security with `owner_uid`
- Validate all user input according to artifact type rules

### 5. Performance Considerations

- Use `select_related()` and `prefetch_related()` for foreign keys
- Implement proper database indexes
- Use pagination for all list endpoints

### 6. API Design Consistency

- Follow RESTful patterns with nested routing
- Provide consistent error responses
- Support filtering and search across all list endpoints

### 7. Local Development Focus

- Optimize for single-developer local machine usage
- Use SQLite for simplicity and portability
- Include management commands for sample data generation

---

This instruction file should guide all development decisions for the DEADLINE project, ensuring consistency with the architectural patterns, business requirements, and Django/DRF best practices.
