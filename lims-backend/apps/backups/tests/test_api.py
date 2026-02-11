from pathlib import Path

import pytest
from django.contrib.auth.models import Permission
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.backups.models import BackupArtifact


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user(db):
    user = User.objects.create_user(
        username="admin_backups",
        email="admin_backups@example.com",
        password="pass123",
        full_name="Admin User",
        role="Admin",
    )
    perms = Permission.objects.filter(
        codename__in=[
            "can_create_backup",
            "can_restore_backup",
            "can_download_backup",
            "can_delete_backup",
        ]
    )
    user.user_permissions.set(perms)
    return user


@pytest.fixture
def regular_user(db):
    return User.objects.create_user(
        username="regular_backups",
        email="regular_backups@example.com",
        password="pass123",
        full_name="Regular User",
        role="Receptionist",
    )


@pytest.mark.django_db
def test_restore_forbidden_for_non_authorized_user(api_client, regular_user, tmp_path):
    backup_file = tmp_path / "backup.zip"
    backup_file.write_bytes(b"x")
    artifact = BackupArtifact.objects.create(
        type="MANUAL",
        status="SUCCESS",
        filename=str(backup_file),
    )

    api_client.force_authenticate(user=regular_user)
    response = api_client.post(
        f"/api/v1/backups/{artifact.id}/restore/",
        {"confirmation": f"RESTORE {artifact.id}"},
        format="json",
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_download_endpoint_auth_and_stream(api_client, admin_user, tmp_path):
    backup_file = tmp_path / "backup.zip"
    backup_file.write_bytes(b"zip-data")
    artifact = BackupArtifact.objects.create(
        created_by=admin_user,
        type="MANUAL",
        status="SUCCESS",
        filename=str(backup_file),
    )

    unauth_response = api_client.get(f"/api/v1/backups/{artifact.id}/download/")
    assert unauth_response.status_code in {status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN}

    api_client.force_authenticate(user=admin_user)
    auth_response = api_client.get(f"/api/v1/backups/{artifact.id}/download/")
    assert auth_response.status_code == status.HTTP_200_OK
    assert "application/zip" in auth_response.get("Content-Type", "")
    assert Path(artifact.filename).name in auth_response.get("Content-Disposition", "")
