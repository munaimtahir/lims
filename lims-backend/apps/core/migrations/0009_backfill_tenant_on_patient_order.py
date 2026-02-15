# Data migration: backfill tenant on Patient and Order where NULL

from django.db import migrations


def get_default_tenant(apps):
    Tenant = apps.get_model("core", "Tenant")
    tenant, _ = Tenant.objects.get_or_create(
        code="LAB", defaults={"name": "Default Lab", "is_active": True}
    )
    return tenant


def backfill_tenant(apps, schema_editor):
    Patient = apps.get_model("patients", "Patient")
    Order = apps.get_model("orders", "Order")
    default_tenant = get_default_tenant(apps)

    # Patients: infer from created_by.tenant if possible, else default
    for p in Patient.objects.filter(tenant__isnull=True).select_related("created_by"):
        if getattr(p.created_by, "tenant_id", None):
            p.tenant_id = p.created_by.tenant_id
        else:
            p.tenant_id = default_tenant.pk
        p.save(update_fields=["tenant_id"])

    # Orders: infer from ordered_by.tenant if possible, else default
    for o in Order.objects.filter(tenant__isnull=True).select_related("ordered_by"):
        if getattr(o.ordered_by, "tenant_id", None):
            o.tenant_id = o.ordered_by.tenant_id
        else:
            o.tenant_id = default_tenant.pk
        o.save(update_fields=["tenant_id"])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0008_add_tenant_settings"),
        ("patients", "0007_patient_tenant_alter_patient_mrn_and_more"),
        ("orders", "0008_order_orders_orde_referre_ea752f_idx"),
    ]

    operations = [
        migrations.RunPython(backfill_tenant, noop),
    ]
