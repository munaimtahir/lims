from django.db import migrations


GROUPS = ["Administrator", "Manager", "Pathologist"]
PERMISSIONS = [
    "can_create_backup",
    "can_restore_backup",
    "can_download_backup",
    "can_delete_backup",
]


def assign_backup_permissions(apps, schema_editor):
    ContentType = apps.get_model("contenttypes", "ContentType")
    Permission = apps.get_model("auth", "Permission")
    Group = apps.get_model("auth", "Group")

    content_type, _ = ContentType.objects.get_or_create(
        app_label="backups",
        model="backupartifact",
    )

    for codename in PERMISSIONS:
        permission, _ = Permission.objects.get_or_create(
            content_type=content_type,
            codename=codename,
            defaults={"name": codename.replace("_", " ").title()},
        )

        for group_name in GROUPS:
            group, _ = Group.objects.get_or_create(name=group_name)
            group.permissions.add(permission)


def reverse_assign_backup_permissions(apps, schema_editor):
    # Keep group-permission mappings on reverse to avoid removing explicit grants.
    return


class Migration(migrations.Migration):
    dependencies = [
        ("backups", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(assign_backup_permissions, reverse_assign_backup_permissions),
    ]
