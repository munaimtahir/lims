import json
import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model

from apps.backups.models import BackupStatus
from apps.backups.services import perform_backup_job, validate_backup_zip


@pytest.mark.django_db
@patch("apps.backups.services._run_command")
def test_perform_backup_job_success(mock_run, settings, tmp_path):
    settings.BACKUP_ROOT = str(tmp_path / "backups")
    settings.MEDIA_ROOT = str(tmp_path / "media")
    Path(settings.MEDIA_ROOT).mkdir(parents=True, exist_ok=True)
    (Path(settings.MEDIA_ROOT) / "note.txt").write_text("abc", encoding="utf-8")

    def _fake_run(command, env):
        output = Path(command[-1])
        output.write_bytes(b"dummy-db")

        class Result:
            stdout = "ok"
            stderr = ""

        return Result()

    mock_run.side_effect = _fake_run

    user = get_user_model().objects.create_user(
        username="admin",
        email="admin@example.com",
        password="x",
        full_name="Admin",
        role="Admin",
    )

    artifact = perform_backup_job(backup_id=None, backup_type="MANUAL", push_offsite=False)
    artifact.refresh_from_db()

    assert artifact.status == BackupStatus.SUCCESS
    assert artifact.size_bytes > 0
    assert Path(artifact.filename).exists()


@pytest.mark.django_db
def test_validate_backup_zip(settings, tmp_path):
    settings.BACKUP_ROOT = str(tmp_path / "backups")
    zip_path = tmp_path / "sample.zip"

    meta = {"k": "v"}
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("db.dump", b"db")
        zf.writestr("files.tar.gz", b"files")
        zf.writestr("meta.json", json.dumps(meta))

    parsed = validate_backup_zip(zip_path)
    assert parsed["k"] == "v"
