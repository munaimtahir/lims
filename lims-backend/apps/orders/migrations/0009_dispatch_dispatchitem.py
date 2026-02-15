# Dispatch and DispatchItem for Phase-1B branch → main lab workflow

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0008_add_tenant_settings"),
        ("orders", "0008_order_orders_orde_referre_ea752f_idx"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Dispatch",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("CREATED", "Created"),
                            ("IN_TRANSIT", "In Transit"),
                            ("RECEIVED", "Received"),
                        ],
                        default="CREATED",
                        max_length=20,
                    ),
                ),
                ("sent_at", models.DateTimeField(blank=True, null=True)),
                ("received_at", models.DateTimeField(blank=True, null=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="dispatches_created",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "from_branch",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="dispatches_sent",
                        to="core.branch",
                    ),
                ),
                (
                    "received_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="dispatches_received",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "tenant",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="dispatches",
                        to="core.tenant",
                    ),
                ),
                (
                    "to_branch",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="dispatches_received",
                        to="core.branch",
                    ),
                ),
            ],
            options={
                "db_table": "orders_dispatch",
                "ordering": ["-created_at"],
                "verbose_name": "Dispatch",
                "verbose_name_plural": "Dispatches",
            },
        ),
        migrations.CreateModel(
            name="DispatchItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "dispatch",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="items",
                        to="orders.dispatch",
                    ),
                ),
                (
                    "order",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="dispatch_items",
                        to="orders.order",
                    ),
                ),
            ],
            options={
                "db_table": "orders_dispatch_item",
                "ordering": ["created_at"],
                "unique_together": {("dispatch", "order")},
            },
        ),
    ]
