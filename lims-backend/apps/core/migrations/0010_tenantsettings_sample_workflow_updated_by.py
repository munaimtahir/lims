# Generated manually for Sample Workflow optional module

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0009_backfill_tenant_on_patient_order"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="tenantsettings",
            name="sample_workflow_enabled",
            field=models.BooleanField(
                default=True,
                help_text="When True, sample collection/receiving is required before result entry. When False, orders go directly to result entry after receipt/payment.",
            ),
        ),
        migrations.AddField(
            model_name="tenantsettings",
            name="updated_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to=settings.AUTH_USER_MODEL,
                help_text="User who last updated these settings.",
            ),
        ),
    ]
