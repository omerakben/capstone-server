#!/usr/bin/env python
"""Debug script to test queryset with select_related."""

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

print("Testing queryset patterns from the view:")

# Simulate the view's get_queryset logic
workspace_id = 4
workspace = Workspace.objects.get(id=workspace_id)
print(f"Found workspace: {workspace.name}")

print("\n1. Basic queryset:")
try:
    queryset = Artifact.objects.filter(workspace=workspace)
    print(f"   Count: {queryset.count()}")
    for artifact in queryset:
        print(f"   Artifact {artifact.id}: {artifact.kind}")
except Exception as e:
    print(f"   ERROR: {e}")
    import traceback

    traceback.print_exc()

print("\n2. Queryset with basic select_related:")
try:
    queryset = Artifact.objects.filter(workspace=workspace).select_related("workspace")
    print(f"   Count: {queryset.count()}")
    for artifact in queryset:
        print(f"   Artifact {artifact.id}: {artifact.kind}")
except Exception as e:
    print(f"   ERROR: {e}")
    import traceback

    traceback.print_exc()

print("\n3. Queryset with workspace_env select_related:")
try:
    queryset = Artifact.objects.filter(workspace=workspace).select_related(
        "workspace", "workspace_env"
    )
    print(f"   Count: {queryset.count()}")
    for artifact in queryset:
        print(
            f"   Artifact {artifact.id}: {artifact.kind}, workspace_env: {artifact.workspace_env}"
        )
except Exception as e:
    print(f"   ERROR: {e}")
    import traceback

    traceback.print_exc()

print("\n4. Full queryset from view (problematic one):")
try:
    queryset = Artifact.objects.filter(workspace=workspace).select_related(
        "workspace",
        "workspace_env",
        "workspace_env__environment_type",
    )
    print(f"   Count: {queryset.count()}")
    for artifact in queryset:
        print(f"   Artifact {artifact.id}: {artifact.kind}")
        print(f"     workspace_env: {artifact.workspace_env}")
        print(
            f"     environment_type: {artifact.workspace_env.environment_type if artifact.workspace_env else 'None'}"
        )
except Exception as e:
    print(f"   ERROR: {e}")
    import traceback

    traceback.print_exc()

print("\n5. Test with environment filter:")
try:
    queryset = Artifact.objects.filter(workspace=workspace).select_related(
        "workspace",
        "workspace_env",
        "workspace_env__environment_type",
    )
    # Apply environment filter like in the view
    env_queryset = queryset.filter(workspace_env__environment_type__slug="DEV")
    print(f"   Count: {env_queryset.count()}")
    for artifact in env_queryset:
        print(f"   Artifact {artifact.id}: {artifact.kind}")
except Exception as e:
    print(f"   ERROR: {e}")
    import traceback

    traceback.print_exc()

print("\n6. Test serializer with problematic queryset:")
from artifacts.serializers import ArtifactSerializer

try:
    queryset = Artifact.objects.filter(workspace=workspace).select_related(
        "workspace",
        "workspace_env",
        "workspace_env__environment_type",
    )
    env_queryset = queryset.filter(workspace_env__environment_type__slug="DEV")

    for artifact in env_queryset:
        serializer = ArtifactSerializer(artifact)
        data = serializer.data
        print(f"   Artifact {artifact.id} serialized: OK")

except Exception as e:
    print(f"   ERROR: {e}")
    import traceback

    traceback.print_exc()
