from django.db import migrations


def backfill_workspace_env(apps, schema_editor):
    Artifact = apps.get_model("artifacts", "Artifact")
    Workspace = apps.get_model("workspaces", "Workspace")
    EnvironmentType = apps.get_model("workspaces", "EnvironmentType")
    WorkspaceEnvironment = apps.get_model("workspaces", "WorkspaceEnvironment")

    # Map slugs to EnvironmentType ids
    env_map = {e.slug: e.id for e in EnvironmentType.objects.all()}

    for art in Artifact.objects.select_related("workspace").all():
        slug = art.environment or "DEV"
        ws = art.workspace
        et_id = env_map.get(slug)
        if not et_id:
            # Skip if unknown slug (shouldn't happen if seeded)
            continue
        # Ensure WorkspaceEnvironment exists
        we, _ = WorkspaceEnvironment.objects.get_or_create(
            workspace_id=ws.id, environment_type_id=et_id
        )
        # Link artifact
        if art.workspace_env_id != we.id:
            art.workspace_env_id = we.id
            art.save(update_fields=["workspace_env_id"])


class Migration(migrations.Migration):

    dependencies = [
        ("artifacts", "0002_workspace_env_fk"),
        ("workspaces", "0002_environment_models"),
    ]

    operations = [
        migrations.RunPython(backfill_workspace_env, migrations.RunPython.noop),
    ]
