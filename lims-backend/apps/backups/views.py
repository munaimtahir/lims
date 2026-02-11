from pathlib import Path
import contextlib

from django.http import FileResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from .models import BackupArtifact
from .permissions import BackupPermission
from .serializers import (
    BackupArtifactSerializer,
    BackupCreateSerializer,
    BackupImportSerializer,
    BackupRestoreSerializer,
    BackupSettingsSerializer,
)
from .services import (
    backup_settings_payload,
    enqueue_backup,
    enqueue_offsite_push,
    enqueue_restore,
    import_backup_file,
    offsite_test_connection,
)


class BackupArtifactViewSet(viewsets.ModelViewSet):
    queryset = BackupArtifact.objects.all().select_related("created_by")
    serializer_class = BackupArtifactSerializer
    permission_classes = [BackupPermission]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def create(self, request, *args, **kwargs):
        serializer = BackupCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        artifact = enqueue_backup(
            created_by=request.user,
            backup_type="MANUAL",
            push_offsite=serializer.validated_data["push_offsite"],
        )
        return Response(BackupArtifactSerializer(artifact).data, status=status.HTTP_202_ACCEPTED)

    def destroy(self, request, *args, **kwargs):
        artifact = self.get_object()
        if artifact.filename:
            with contextlib.suppress(Exception):
                Path(artifact.filename).unlink(missing_ok=True)
        artifact.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["get"])
    def download(self, request, pk=None):
        artifact = self.get_object()
        file_path = Path(artifact.filename)
        if not artifact.filename or not file_path.exists():
            return Response({"detail": "Backup file not found"}, status=status.HTTP_404_NOT_FOUND)

        return FileResponse(
            file_path.open("rb"),
            content_type="application/zip",
            as_attachment=True,
            filename=file_path.name,
        )

    @action(detail=True, methods=["post"])
    def restore(self, request, pk=None):
        artifact = self.get_object()
        serializer = BackupRestoreSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        expected = f"RESTORE {artifact.id}"
        if serializer.validated_data["confirmation"] != expected:
            return Response(
                {"detail": f"Invalid confirmation. Expected exact text: {expected}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        enqueue_restore(artifact)
        return Response({"status": "Restore job queued", "backup_id": str(artifact.id)}, status=status.HTTP_202_ACCEPTED)

    @action(detail=False, methods=["post"], url_path="import")
    def import_backup(self, request):
        serializer = BackupImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        artifact = import_backup_file(serializer.validated_data["file"], created_by=request.user)
        return Response(BackupArtifactSerializer(artifact).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def push(self, request, pk=None):
        artifact = self.get_object()
        enqueue_offsite_push(artifact)
        artifact.refresh_from_db()
        return Response(BackupArtifactSerializer(artifact).data, status=status.HTTP_202_ACCEPTED)

    @action(detail=False, methods=["get"], url_path="settings")
    def backup_settings(self, request):
        payload = backup_settings_payload()
        return Response(BackupSettingsSerializer(payload).data)

    @action(detail=False, methods=["post"], url_path="offsite-test")
    def offsite_test(self, request):
        payload = offsite_test_connection()
        code = status.HTTP_200_OK if payload.get("ok") else status.HTTP_400_BAD_REQUEST
        return Response(payload, status=code)
