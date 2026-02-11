from rest_framework import serializers

from .models import BackupArtifact


class BackupArtifactSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source="created_by.full_name", read_only=True)

    class Meta:
        model = BackupArtifact
        fields = [
            "id",
            "created_at",
            "updated_at",
            "created_by",
            "created_by_name",
            "type",
            "status",
            "filename",
            "size_bytes",
            "checksum_sha256",
            "meta",
            "offsite_provider",
            "offsite_status",
            "logs",
            "error_message",
        ]


class BackupCreateSerializer(serializers.Serializer):
    push_offsite = serializers.BooleanField(default=False)


class BackupImportSerializer(serializers.Serializer):
    file = serializers.FileField()


class BackupRestoreSerializer(serializers.Serializer):
    confirmation = serializers.CharField()


class BackupSettingsSerializer(serializers.Serializer):
    retention_daily = serializers.IntegerField()
    retention_weekly = serializers.IntegerField()
    retention_monthly = serializers.IntegerField()
    offsite_provider = serializers.CharField()
    offsite_configured = serializers.BooleanField()
