#!/usr/bin/env python
"""Debug script to check artifact-tag relationships."""

import os
import sys

import django

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "deadline_api.settings")
django.setup()

from artifacts.models import Artifact, ArtifactTag, Tag

print("All ArtifactTag relationships:")
for at in ArtifactTag.objects.all():
    try:
        print(f"  ArtifactTag {at.id}: artifact {at.artifact_id} -> tag {at.tag_id}")
        print(
            f"    Artifact exists: {Artifact.objects.filter(id=at.artifact_id).exists()}"
        )
        print(f"    Tag exists: {Tag.objects.filter(id=at.tag_id).exists()}")
        if Tag.objects.filter(id=at.tag_id).exists():
            tag = Tag.objects.get(id=at.tag_id)
            print(f"    Tag workspace: {tag.workspace_id}")
        if Artifact.objects.filter(id=at.artifact_id).exists():
            artifact = Artifact.objects.get(id=at.artifact_id)
            print(f"    Artifact workspace: {artifact.workspace.id}")
    except Exception as e:
        print(f"    ERROR accessing relationship: {e}")

print("\nTesting artifact tag access:")
for artifact in Artifact.objects.all():
    try:
        print(f"Artifact {artifact.id}: {artifact.kind}")
        tags = artifact.tags.all()
        print(f"  Tags: {list(tags)}")
        tag_objects = [{"id": t.id, "name": t.name} for t in tags.order_by("name")]
        print(f"  Tag objects: {tag_objects}")
    except Exception as e:
        print(f"  ERROR: {e}")

print("\nDirect serializer test:")
from artifacts.serializers import ArtifactSerializer

for artifact in Artifact.objects.all():
    try:
        serializer = ArtifactSerializer(artifact)
        data = serializer.data
        print(f"Artifact {artifact.id} serialized successfully")
        print(f"  Tag objects: {data.get('tag_objects', 'MISSING')}")
    except Exception as e:
        print(f"Artifact {artifact.id} serialization ERROR: {e}")
        import traceback

        traceback.print_exc()
