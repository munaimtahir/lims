from django.core.management.base import BaseCommand

from apps.backups.services import apply_retention_policy, enqueue_backup


class Command(BaseCommand):
    help = "Create scheduled automatic backup and apply retention policy."

    def handle(self, *args, **options):
        artifact = enqueue_backup(created_by=None, backup_type="AUTO", push_offsite=True)
        apply_retention_policy()
        self.stdout.write(
            self.style.SUCCESS(f"Scheduled backup enqueued: {artifact.id}")
        )
