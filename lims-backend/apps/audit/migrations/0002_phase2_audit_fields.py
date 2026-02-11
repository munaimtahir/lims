# Generated manually for Phase 2 hardening.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("audit", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="auditlog",
            name="actor",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="audit_events",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="auditlog",
            name="after",
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="auditlog",
            name="before",
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="auditlog",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, db_index=True, null=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="auditlog",
            name="entity_id",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="auditlog",
            name="entity_type",
            field=models.CharField(blank=True, db_index=True, default="", max_length=100),
        ),
        migrations.AddField(
            model_name="auditlog",
            name="metadata",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="auditlog",
            name="source",
            field=models.CharField(
                choices=[("api", "API"), ("admin", "Admin"), ("system", "System")],
                default="api",
                max_length=20,
            ),
        ),
        migrations.RunSQL(
            sql="""
            UPDATE audit_logs
            SET
              created_at = COALESCE(created_at, timestamp),
              entity_type = CASE WHEN entity_type = '' THEN COALESCE(table_name, '') ELSE entity_type END,
              entity_id = CASE WHEN entity_id = '' THEN COALESCE(object_id, '') ELSE entity_id END,
              before = COALESCE(before, old_value),
              after = COALESCE(after, new_value),
              actor_id = COALESCE(actor_id, user_id);
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
