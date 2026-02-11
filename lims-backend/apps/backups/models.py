import uuid

from django.conf import settings
from django.db import models


class BackupType(models.TextChoices):
    AUTO = "AUTO", "Automatic"
    MANUAL = "MANUAL", "Manual"
    IMPORTED = "IMPORTED", "Imported"


class BackupStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    RUNNING = "RUNNING", "Running"
    SUCCESS = "SUCCESS", "Success"
    FAILED = "FAILED", "Failed"


class OffsiteProvider(models.TextChoices):
    NONE = "NONE", "None"
    S3 = "S3", "S3"
    GDRIVE = "GDRIVE", "Google Drive"


class OffsiteStatus(models.TextChoices):
    NOT_CONFIGURED = "NOT_CONFIGURED", "Not configured"
    PENDING = "PENDING", "Pending"
    SUCCESS = "SUCCESS", "Success"
    FAILED = "FAILED", "Failed"


def generate_backup_id() -> str:
    return str(uuid.uuid4())


class BackupArtifact(models.Model):
    id = models.CharField(
        primary_key=True,
        max_length=36,
        default=generate_backup_id,
        editable=False,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="backups_created",
    )
    type = models.CharField(max_length=16, choices=BackupType.choices, default=BackupType.MANUAL)
    status = models.CharField(max_length=16, choices=BackupStatus.choices, default=BackupStatus.PENDING)
    filename = models.CharField(max_length=1024, blank=True, default="")
    size_bytes = models.BigIntegerField(default=0)
    checksum_sha256 = models.CharField(max_length=64, blank=True, default="")
    meta = models.JSONField(default=dict, blank=True)
    offsite_provider = models.CharField(
        max_length=16,
        choices=OffsiteProvider.choices,
        default=OffsiteProvider.NONE,
    )
    offsite_status = models.CharField(
        max_length=20,
        choices=OffsiteStatus.choices,
        default=OffsiteStatus.NOT_CONFIGURED,
    )
    logs = models.TextField(blank=True, default="")
    error_message = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-created_at"]
        permissions = [
            ("can_create_backup", "Can create backup artifacts"),
            ("can_restore_backup", "Can restore backup artifacts"),
            ("can_download_backup", "Can download backup artifacts"),
            ("can_delete_backup", "Can delete backup artifacts"),
        ]

    def __str__(self):
        return f"{self.id} ({self.type}) {self.status}"
