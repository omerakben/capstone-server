#!/usr/bin/env python
"""Debug script to test artifact retrieval."""

import os
import sys

import django

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "deadline_api.settings")
django.setup()

from artifacts.models import Artifact
from workspaces.models import Workspace

# Get all workspaces
print("All Workspaces:")
for ws in Workspace.objects.all():
    print(f"  Workspace {ws.id}: {ws.name} (owner: {ws.owner_uid})")

print("\nAll Artifacts:")
for artifact in Artifact.objects.all():
    print(
        f"  Artifact {artifact.id}: {artifact.kind} '{artifact.key}' in workspace {artifact.workspace.id}"
    )
    print(f"    workspace_env: {artifact.workspace_env}")
    print(f"    environment: {artifact.environment}")

# Test the failing query
print("\nTesting DEV environment filter:")
workspace_id = 4
queryset = Artifact.objects.filter(workspace__id=workspace_id)
print(f"Base queryset count: {queryset.count()}")

try:
    # Try the new filter
    print("Trying new filter (workspace_env__environment_type__slug=DEV):")
    new_filter = queryset.filter(workspace_env__environment_type__slug="DEV")
    print(f"New filter count: {new_filter.count()}")

except Exception as e:
    print(f"New filter error: {e}")

    # Try the fallback
    print("Trying fallback filter (environment=DEV):")
    fallback_filter = queryset.filter(environment="DEV")
    print(f"Fallback filter count: {fallback_filter.count()}")

# Check WorkspaceEnvironment relationships
print("\nChecking WorkspaceEnvironment relationships:")
from workspaces.models import WorkspaceEnvironment

for we in WorkspaceEnvironment.objects.all():
    print(f"  WE {we.id}: workspace {we.workspace.id}, env_type {we.environment_type}")
