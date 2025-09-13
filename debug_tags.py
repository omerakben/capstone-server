#!/usr/bin/env python3
import os
import sys

import django

# Configure Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "deadline_api.settings")
sys.path.append("/Users/ozzy-mac/Projects/DEADLINE/capstone-server")
django.setup()

from artifacts.models import Artifact, ArtifactTag, Tag
from workspaces.models import Workspace

print("=== Database State Diagnosis ===\n")

print("=== Tags ===")
for t in Tag.objects.all():
    print(f"Tag {t.id}: '{t.name}' (workspace {t.workspace_id})")

print("\n=== Artifacts ===")
for a in Artifact.objects.all():
    print(f"Artifact {a.id}: '{a.primary_identifier()}' (workspace {a.workspace_id})")

print("\n=== ArtifactTags ===")
for at in ArtifactTag.objects.all():
    print(f"ArtifactTag {at.id}: artifact {at.artifact_id} <-> tag {at.tag_id}")

print("\n=== Checking constraint violations ===")
for at in ArtifactTag.objects.select_related("artifact", "tag"):
    if at.artifact.workspace_id != at.tag.workspace_id:
        print(
            f"VIOLATION: ArtifactTag {at.id} links artifact {at.artifact_id} (workspace {at.artifact.workspace_id}) with tag {at.tag_id} (workspace {at.tag.workspace_id})"
        )

print("\n=== Attempting to reproduce the error ===")
try:
    artifact = Artifact.objects.get(id=3)
    print(
        f"Found artifact {artifact.id}: {artifact.primary_identifier()} in workspace {artifact.workspace_id}"
    )

    tags = Tag.objects.filter(workspace_id=artifact.workspace_id)
    print(f"Available tags in same workspace: {[f'{t.id}:{t.name}' for t in tags]}")

    # Try to set tags
    print("Attempting to set tags...")
    artifact.tags.set(tags)
    print("Success! Tags set without error.")

except Exception as e:
    print(f"Error: {e}")
    import traceback

    traceback.print_exc()
