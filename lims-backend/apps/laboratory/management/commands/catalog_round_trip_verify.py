"""
Verify catalog export/import round-trip produces no changes.
"""
from io import BytesIO
from django.core.management.base import BaseCommand
from apps.laboratory.catalog_io import export_catalog_workbook, import_catalog_from_excel


class Command(BaseCommand):
    help = "Verify export -> import(dry_run, strict) is a no-op"

    def handle(self, *args, **options):
        workbook = export_catalog_workbook()
        buffer = BytesIO()
        workbook.save(buffer)
        buffer.seek(0)

        result = import_catalog_from_excel(
            buffer,
            strict=True,
            allow_defaults=False,
            mode="upsert",
            dry_run=True,
        )

        errors = result.get("errors", [])
        counts = result.get("counts", {})
        changes = []
        for key, group in counts.items():
            if group.get("created") or group.get("updated"):
                changes.append(f"{key}: created={group.get('created')} updated={group.get('updated')}")

        if errors or changes:
            self.stdout.write(self.style.ERROR("Round-trip verification failed"))
            if errors:
                self.stdout.write(self.style.ERROR(f"Errors: {len(errors)}"))
                for error in errors[:10]:
                    self.stdout.write(self.style.ERROR(f"  [{error['sheet']}] Row {error['row']}: {error['message']}"))
            if changes:
                self.stdout.write(self.style.ERROR("Changes detected: " + ", ".join(changes)))
            return 1

        self.stdout.write(self.style.SUCCESS("Round-trip verification passed (no changes)"))
        return 0
