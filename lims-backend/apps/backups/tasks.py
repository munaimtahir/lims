from celery import shared_task

from .services import (
    apply_retention_policy,
    perform_backup_job,
    perform_offsite_push,
    perform_restore_job,
)


@shared_task(bind=True)
def backup_create_task(self, backup_id: str, push_offsite: bool = False):
    perform_backup_job(backup_id=backup_id, push_offsite=push_offsite)


@shared_task(bind=True)
def backup_restore_task(self, backup_id: str):
    perform_restore_job(backup_id=backup_id)


@shared_task(bind=True)
def backup_push_task(self, backup_id: str):
    perform_offsite_push(backup_id=backup_id)


@shared_task(bind=True)
def run_scheduled_backups_task(self):
    perform_backup_job(backup_id=None, backup_type="AUTO", push_offsite=True)
    apply_retention_policy()
