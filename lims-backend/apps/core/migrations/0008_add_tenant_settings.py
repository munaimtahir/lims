# Generated manually for TenantSettings (Collection Center optional module)

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0007_tenant_branch_tenantmrnsequence_orderidsequence_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="TenantSettings",
            fields=[
                (
                    "tenant",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        primary_key=True,
                        related_name="settings",
                        serialize=False,
                        to="core.tenant",
                    ),
                ),
                (
                    "enable_collection_centers",
                    models.BooleanField(
                        default=False,
                        help_text="When True, registration/order flows may require or use collection center.",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "default_branch",
                    models.ForeignKey(
                        blank=True,
                        help_text="Default branch for order collection when user has no branch (e.g. HQ).",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to="core.branch",
                    ),
                ),
                (
                    "default_collection_center",
                    models.ForeignKey(
                        blank=True,
                        help_text="Default collection center for patient registration when centers enabled.",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to="core.collectioncenter",
                    ),
                ),
            ],
            options={
                "db_table": "core_tenant_settings",
                "verbose_name": "Tenant settings",
                "verbose_name_plural": "Tenant settings",
            },
        ),
    ]
