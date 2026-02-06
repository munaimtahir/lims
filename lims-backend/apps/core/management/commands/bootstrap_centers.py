"""
Management command to bootstrap collection centers.
"""
from django.core.management.base import BaseCommand
from apps.core.models import CollectionCenter


class Command(BaseCommand):
    help = "Bootstrap collection centers (ensures Head Office exists)"

    def handle(self, *args, **options):
        # Ensure Head Office (00) exists
        center_00, created = CollectionCenter.objects.get_or_create(
            code="00",
            defaults={
                "name": "Head Office",
                "is_active": True,
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f"✓ Created Head Office center: {center_00}")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"✓ Head Office center already exists: {center_00}")
            )
        
        # Optionally create a test center for development
        center_10, created = CollectionCenter.objects.get_or_create(
            code="10",
            defaults={
                "name": "Test Collection Center",
                "is_active": True,
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f"✓ Created test center: {center_10}")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"✓ Test center already exists: {center_10}")
            )
        
        self.stdout.write(
            self.style.SUCCESS("\n✓ Collection centers bootstrapped successfully")
        )
