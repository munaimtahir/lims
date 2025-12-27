# Generated migration to migrate SampleCollection data to Sample model
# This migration should be run after ensuring all code uses Sample model

from django.db import migrations


def migrate_sample_collections_to_samples(apps, schema_editor):
    """
    Migrate SampleCollection data to Sample model.
    
    Note: This migration assumes one Sample per OrderItem.
    If a SampleCollection has multiple OrderItems, it creates one Sample per OrderItem.
    """
    SampleCollection = apps.get_model('samples', 'SampleCollection')
    Sample = apps.get_model('samples', 'Sample')
    OrderItem = apps.get_model('orders', 'OrderItem')
    
    # Status mapping from SampleCollection to Sample
    status_mapping = {
        'pending': 'PENDING',
        'collected': 'COLLECTED',
        'received': 'RECEIVED',
        'rejected': 'REJECTED',
    }
    
    # Migrate each SampleCollection
    for collection in SampleCollection.objects.all():
        # Get all order items for this collection
        order_items = collection.order_items.all()
        
        # If no order items, skip (shouldn't happen, but safety check)
        if not order_items.exists():
            continue
        
        # Create one Sample per OrderItem
        for order_item in order_items:
            # Map status
            sample_status = status_mapping.get(collection.status, 'PENDING')
            
            # Create Sample
            Sample.objects.create(
                order_item=order_item,
                sample_type=collection.sample_type,
                barcode=collection.barcode or f"MIG-{collection.id}-{order_item.id}",
                collected_at=collection.collected_at,
                collected_by=collection.collected_by,
                status=sample_status,
                notes=collection.notes,
                # received_at and received_by will be set separately if needed
            )


def reverse_migration(apps, schema_editor):
    """
    Reverse migration - not recommended as SampleCollection is deprecated.
    This is a placeholder for migration rollback capability.
    """
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('samples', '0001_initial'),
        ('orders', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            migrate_sample_collections_to_samples,
            reverse_migration,
        ),
    ]

