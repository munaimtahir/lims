import contextlib
import hashlib
import json
import os
import shutil
import socket
import subprocess
import tarfile
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
from django.utils import timezone

from .models import BackupArtifact, BackupStatus, BackupType, OffsiteProvider, OffsiteStatus

REQUIRED_ARTIFACT_FILES = {"db.dump", "files.tar.gz", "meta.json"}


def _backup_root() -> Path:
    root = Path(getattr(settings, "BACKUP_ROOT", "/backups/lims"))
    root.mkdir(parents=True, exist_ok=True)
    return root


def _app_name() -> str:
    return getattr(settings, "BACKUP_APP_NAME", "lims")


def _media_root() -> Path:
    return Path(settings.MEDIA_ROOT)


def _append_log(artifact: BackupArtifact, message: str) -> None:
    timestamp = timezone.now().isoformat()
    artifact.logs = f"{artifact.logs}\n[{timestamp}] {message}".strip()
    artifact.save(update_fields=["logs", "updated_at"])


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _build_db_command(output_file: Path) -> tuple[list[str], dict[str, str]]:
    db = settings.DATABASES["default"]
    env = os.environ.copy()
    env["PGPASSWORD"] = str(db.get("PASSWORD") or "")
    command = [
        "pg_dump",
        "-Fc",
        "-h",
        str(db.get("HOST") or "localhost"),
        "-p",
        str(db.get("PORT") or "5432"),
        "-U",
        str(db.get("USER") or "postgres"),
        "-d",
        str(db.get("NAME") or "postgres"),
        "-f",
        str(output_file),
    ]
    return command, env


def _build_restore_command(dump_file: Path) -> tuple[list[str], dict[str, str]]:
    db = settings.DATABASES["default"]
    env = os.environ.copy()
    env["PGPASSWORD"] = str(db.get("PASSWORD") or "")
    command = [
        "pg_restore",
        "--clean",
        "--if-exists",
        "--no-owner",
        "--no-privileges",
        "-h",
        str(db.get("HOST") or "localhost"),
        "-p",
        str(db.get("PORT") or "5432"),
        "-U",
        str(db.get("USER") or "postgres"),
        "-d",
        str(db.get("NAME") or "postgres"),
        str(dump_file),
    ]
    return command, env


def _run_command(command: list[str], env: dict[str, str]) -> subprocess.CompletedProcess:
    return subprocess.run(command, env=env, check=True, capture_output=True, text=True)


def _snapshot_config() -> dict[str, Any]:
    project_root = Path(settings.BASE_DIR).parent
    compose_candidates = [
        project_root / "docker-compose.yml",
        project_root / "compose.prod.yml",
    ]
    compose_files = [str(p) for p in compose_candidates if p.exists()]

    safe_env_keys = [
        "DJANGO_SETTINGS_MODULE",
        "DB_HOST",
        "DB_PORT",
        "DB_NAME",
        "BACKUP_ROOT",
        "BACKUP_OFFSITE_PROVIDER",
        "S3_BUCKET",
        "S3_ENDPOINT_URL",
        "AWS_DEFAULT_REGION",
    ]
    safe_env = {k: os.environ.get(k, "") for k in safe_env_keys}

    git_commit = ""
    with contextlib.suppress(Exception):
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=project_root,
            check=True,
            capture_output=True,
            text=True,
        )
        git_commit = proc.stdout.strip()

    return {
        "compose_files": compose_files,
        "safe_env": safe_env,
        "git_commit": git_commit,
    }


def _make_checksums(directory: Path, file_names: list[str]) -> Path:
    checksums_path = directory / "checksums.sha256"
    lines: list[str] = []
    for name in file_names:
        digest = _sha256_file(directory / name)
        lines.append(f"{digest}  {name}")
    checksums_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return checksums_path


def _validate_manifest(zf: zipfile.ZipFile) -> dict[str, Any]:
    names = set(zf.namelist())
    missing = REQUIRED_ARTIFACT_FILES - names
    if missing:
        raise ValueError(f"Backup zip missing required files: {sorted(missing)}")

    meta = json.loads(zf.read("meta.json").decode("utf-8"))

    if "checksums.sha256" in names:
        checksums_raw = zf.read("checksums.sha256").decode("utf-8").strip()
        for line in checksums_raw.splitlines():
            digest, file_name = line.split("  ", 1)
            payload = zf.read(file_name)
            calculated = hashlib.sha256(payload).hexdigest()
            if calculated != digest:
                raise ValueError(f"Checksum mismatch for {file_name}")
    return meta


def validate_backup_zip(path: Path) -> dict[str, Any]:
    with zipfile.ZipFile(path, "r") as zf:
        return _validate_manifest(zf)


def _make_filename(artifact: BackupArtifact) -> str:
    stamp = timezone.now().strftime("%Y%m%d_%H%M%S")
    return f"{stamp}_{artifact.type.lower()}_{artifact.id}.zip"


def enqueue_backup(created_by=None, backup_type: str = BackupType.MANUAL, push_offsite: bool = False) -> BackupArtifact:
    from .tasks import backup_create_task

    artifact = BackupArtifact.objects.create(
        created_by=created_by,
        type=backup_type,
        status=BackupStatus.PENDING,
        offsite_status=OffsiteStatus.PENDING if push_offsite else OffsiteStatus.NOT_CONFIGURED,
    )
    backup_create_task.delay(str(artifact.id), push_offsite=push_offsite)
    return artifact


def perform_backup_job(backup_id: str | None, backup_type: str = BackupType.MANUAL, push_offsite: bool = False) -> BackupArtifact:
    if backup_id:
        artifact = BackupArtifact.objects.get(id=backup_id)
    else:
        artifact = BackupArtifact.objects.create(
            type=backup_type,
            status=BackupStatus.PENDING,
            offsite_status=OffsiteStatus.PENDING if push_offsite else OffsiteStatus.NOT_CONFIGURED,
        )

    artifact.status = BackupStatus.RUNNING
    artifact.error_message = ""
    artifact.save(update_fields=["status", "error_message", "updated_at"])
    _append_log(artifact, "Backup job started")

    try:
        backup_root = _backup_root()
        with tempfile.TemporaryDirectory(prefix="lims_backup_") as temp_dir:
            temp_path = Path(temp_dir)
            db_dump = temp_path / "db.dump"
            files_archive = temp_path / "files.tar.gz"
            meta_file = temp_path / "meta.json"
            config_file = temp_path / "config_snapshot.json"

            command, env = _build_db_command(db_dump)
            _append_log(artifact, "Running pg_dump")
            result = _run_command(command, env)
            if result.stdout:
                _append_log(artifact, result.stdout.strip())
            if result.stderr:
                _append_log(artifact, result.stderr.strip())

            _append_log(artifact, "Archiving media files")
            media_root = _media_root()
            with tarfile.open(files_archive, "w:gz") as tf:
                if media_root.exists():
                    tf.add(media_root, arcname="media")

            db_size = db_dump.stat().st_size if db_dump.exists() else 0
            files_size = files_archive.stat().st_size if files_archive.exists() else 0
            meta = {
                "created_at": timezone.now().isoformat(),
                "app_name": _app_name(),
                "hostname": socket.gethostname(),
                "db_name": settings.DATABASES["default"].get("NAME"),
                "backup_type": artifact.type,
                "artifact_id": str(artifact.id),
                "sizes": {
                    "db_dump": db_size,
                    "files_archive": files_size,
                },
            }
            meta_file.write_text(json.dumps(meta, indent=2), encoding="utf-8")
            config_file.write_text(json.dumps(_snapshot_config(), indent=2), encoding="utf-8")

            checksums = _make_checksums(
                temp_path,
                ["db.dump", "files.tar.gz", "meta.json", "config_snapshot.json"],
            )

            out_name = _make_filename(artifact)
            out_path = backup_root / out_name
            _append_log(artifact, f"Creating archive: {out_path}")
            with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
                zf.write(db_dump, arcname="db.dump")
                zf.write(files_archive, arcname="files.tar.gz")
                zf.write(meta_file, arcname="meta.json")
                zf.write(config_file, arcname="config_snapshot.json")
                zf.write(checksums, arcname="checksums.sha256")

        artifact.filename = str(out_path)
        artifact.size_bytes = out_path.stat().st_size
        artifact.checksum_sha256 = _sha256_file(out_path)
        artifact.meta = meta
        artifact.status = BackupStatus.SUCCESS
        if artifact.offsite_status == OffsiteStatus.PENDING and not push_offsite:
            artifact.offsite_status = OffsiteStatus.NOT_CONFIGURED
        artifact.save(
            update_fields=[
                "filename",
                "size_bytes",
                "checksum_sha256",
                "meta",
                "status",
                "offsite_status",
                "updated_at",
            ]
        )
        _append_log(artifact, "Backup completed successfully")

        if push_offsite:
            perform_offsite_push(str(artifact.id))

        return artifact
    except Exception as exc:
        artifact.status = BackupStatus.FAILED
        artifact.error_message = str(exc)
        artifact.save(update_fields=["status", "error_message", "updated_at"])
        _append_log(artifact, f"Backup failed: {exc}")
        raise


def import_backup_file(uploaded_file: UploadedFile, created_by=None) -> BackupArtifact:
    artifact = BackupArtifact.objects.create(
        created_by=created_by,
        type=BackupType.IMPORTED,
        status=BackupStatus.RUNNING,
    )
    _append_log(artifact, "Import started")

    try:
        backup_root = _backup_root()
        temp_name = f"import_{artifact.id}.zip"
        target_path = backup_root / temp_name
        with target_path.open("wb") as out:
            for chunk in uploaded_file.chunks():
                out.write(chunk)

        meta = validate_backup_zip(target_path)
        final_name = _make_filename(artifact)
        final_path = backup_root / final_name
        target_path.rename(final_path)

        artifact.filename = str(final_path)
        artifact.size_bytes = final_path.stat().st_size
        artifact.checksum_sha256 = _sha256_file(final_path)
        artifact.meta = {**meta, "imported": True}
        artifact.status = BackupStatus.SUCCESS
        artifact.save(
            update_fields=[
                "filename",
                "size_bytes",
                "checksum_sha256",
                "meta",
                "status",
                "updated_at",
            ]
        )
        _append_log(artifact, "Import completed")
        return artifact
    except Exception as exc:
        artifact.status = BackupStatus.FAILED
        artifact.error_message = str(exc)
        artifact.save(update_fields=["status", "error_message", "updated_at"])
        _append_log(artifact, f"Import failed: {exc}")
        raise


def enqueue_restore(artifact: BackupArtifact) -> None:
    from .tasks import backup_restore_task

    backup_restore_task.delay(str(artifact.id))


def perform_restore_job(backup_id: str) -> None:
    artifact = BackupArtifact.objects.get(id=backup_id)
    _append_log(artifact, "Restore job started")
    cache.set("maintenance_mode", True, timeout=60 * 60)

    media_root = _media_root()
    media_backup_path = media_root.parent / f"{media_root.name}.bak_{timezone.now().strftime('%Y%m%d_%H%M%S')}"

    try:
        with tempfile.TemporaryDirectory(prefix="lims_restore_") as temp_dir:
            temp_path = Path(temp_dir)
            _append_log(artifact, "Extracting backup zip")
            with zipfile.ZipFile(artifact.filename, "r") as zf:
                _validate_manifest(zf)
                zf.extractall(temp_path)

            db_dump = temp_path / "db.dump"
            files_archive = temp_path / "files.tar.gz"

            _append_log(artifact, "Restoring database with pg_restore")
            command, env = _build_restore_command(db_dump)
            result = _run_command(command, env)
            if result.stdout:
                _append_log(artifact, result.stdout.strip())
            if result.stderr:
                _append_log(artifact, result.stderr.strip())

            _append_log(artifact, "Restoring media files")
            if media_root.exists():
                shutil.move(str(media_root), str(media_backup_path))
            media_root.mkdir(parents=True, exist_ok=True)

            with tarfile.open(files_archive, "r:gz") as tf:
                members = tf.getmembers()
                tf.extractall(path=temp_path, members=members)

            extracted_media = temp_path / "media"
            if extracted_media.exists():
                for item in extracted_media.iterdir():
                    destination = media_root / item.name
                    if destination.exists():
                        if destination.is_dir():
                            shutil.rmtree(destination)
                        else:
                            destination.unlink()
                    shutil.move(str(item), str(destination))

        _append_log(artifact, f"Restore completed. Previous media moved to: {media_backup_path}")
    except Exception as exc:
        _append_log(artifact, f"Restore failed: {exc}")
        raise
    finally:
        cache.set("maintenance_mode", False, timeout=1)


def _offsite_provider() -> str:
    return str(getattr(settings, "BACKUP_OFFSITE_PROVIDER", "none")).strip().lower()


def is_offsite_configured() -> bool:
    provider = _offsite_provider()
    if provider == "s3":
        return bool(
            getattr(settings, "BACKUP_S3_BUCKET", "")
            and os.environ.get("AWS_ACCESS_KEY_ID")
            and os.environ.get("AWS_SECRET_ACCESS_KEY")
        )
    return False


def _build_s3_client():
    import boto3

    params: dict[str, Any] = {
        "aws_access_key_id": os.environ.get("AWS_ACCESS_KEY_ID", ""),
        "aws_secret_access_key": os.environ.get("AWS_SECRET_ACCESS_KEY", ""),
        "region_name": getattr(settings, "BACKUP_S3_REGION", "us-east-1"),
    }
    endpoint_url = getattr(settings, "BACKUP_S3_ENDPOINT_URL", "")
    if endpoint_url:
        params["endpoint_url"] = endpoint_url
    return boto3.client("s3", **params)


def offsite_test_connection() -> dict[str, Any]:
    provider = _offsite_provider()
    if provider != "s3":
        return {"ok": False, "message": "Offsite provider not configured"}

    if not is_offsite_configured():
        return {"ok": False, "message": "S3 credentials/bucket missing"}

    client = _build_s3_client()
    bucket = getattr(settings, "BACKUP_S3_BUCKET", "")
    client.head_bucket(Bucket=bucket)
    return {"ok": True, "message": "S3 connection successful", "provider": "S3"}


def enqueue_offsite_push(artifact: BackupArtifact) -> None:
    from .tasks import backup_push_task

    artifact.offsite_status = OffsiteStatus.PENDING
    artifact.save(update_fields=["offsite_status", "updated_at"])
    backup_push_task.delay(str(artifact.id))


def perform_offsite_push(backup_id: str) -> None:
    artifact = BackupArtifact.objects.get(id=backup_id)
    provider = _offsite_provider()

    if provider != "s3":
        artifact.offsite_provider = OffsiteProvider.NONE
        artifact.offsite_status = OffsiteStatus.NOT_CONFIGURED
        artifact.save(update_fields=["offsite_provider", "offsite_status", "updated_at"])
        _append_log(artifact, "Offsite push skipped: provider not configured")
        return

    if not is_offsite_configured():
        artifact.offsite_provider = OffsiteProvider.S3
        artifact.offsite_status = OffsiteStatus.FAILED
        artifact.error_message = "S3 provider not fully configured"
        artifact.save(
            update_fields=["offsite_provider", "offsite_status", "error_message", "updated_at"]
        )
        _append_log(artifact, "Offsite push failed: missing S3 configuration")
        return

    bucket = getattr(settings, "BACKUP_S3_BUCKET", "")
    key = f"{_app_name()}/backups/{Path(artifact.filename).name}"

    try:
        client = _build_s3_client()
        client.upload_file(artifact.filename, bucket, key)
        meta = dict(artifact.meta or {})
        meta["offsite"] = {
            "provider": "S3",
            "bucket": bucket,
            "key": key,
        }
        artifact.meta = meta
        artifact.offsite_provider = OffsiteProvider.S3
        artifact.offsite_status = OffsiteStatus.SUCCESS
        artifact.save(update_fields=["meta", "offsite_provider", "offsite_status", "updated_at"])
        _append_log(artifact, f"Offsite upload completed: s3://{bucket}/{key}")
    except Exception as exc:
        artifact.offsite_provider = OffsiteProvider.S3
        artifact.offsite_status = OffsiteStatus.FAILED
        artifact.error_message = str(exc)
        artifact.save(
            update_fields=["offsite_provider", "offsite_status", "error_message", "updated_at"]
        )
        _append_log(artifact, f"Offsite upload failed: {exc}")
        raise


def backup_settings_payload() -> dict[str, Any]:
    provider = _offsite_provider()
    return {
        "retention_daily": int(getattr(settings, "BACKUP_RETENTION_DAILY", 7)),
        "retention_weekly": int(getattr(settings, "BACKUP_RETENTION_WEEKLY", 4)),
        "retention_monthly": int(getattr(settings, "BACKUP_RETENTION_MONTHLY", 6)),
        "offsite_provider": provider.upper() if provider else "NONE",
        "offsite_configured": is_offsite_configured(),
    }


def _retention_keep_ids(artifacts: list[BackupArtifact], daily: int, weekly: int, monthly: int) -> set[str]:
    keep: set[str] = set()

    day_seen: set[str] = set()
    week_seen: set[str] = set()
    month_seen: set[str] = set()

    for artifact in artifacts:
        dt = timezone.localtime(artifact.created_at)
        day_key = dt.strftime("%Y-%m-%d")
        week_key = f"{dt.isocalendar().year}-{dt.isocalendar().week:02d}"
        month_key = dt.strftime("%Y-%m")

        if len(day_seen) < daily and day_key not in day_seen:
            day_seen.add(day_key)
            keep.add(str(artifact.id))
        if len(week_seen) < weekly and week_key not in week_seen:
            week_seen.add(week_key)
            keep.add(str(artifact.id))
        if len(month_seen) < monthly and month_key not in month_seen:
            month_seen.add(month_key)
            keep.add(str(artifact.id))

    return keep


def apply_retention_policy() -> dict[str, int]:
    daily = int(getattr(settings, "BACKUP_RETENTION_DAILY", 7))
    weekly = int(getattr(settings, "BACKUP_RETENTION_WEEKLY", 4))
    monthly = int(getattr(settings, "BACKUP_RETENTION_MONTHLY", 6))

    artifacts = list(
        BackupArtifact.objects.filter(type=BackupType.AUTO, status=BackupStatus.SUCCESS).order_by("-created_at")
    )
    keep_ids = _retention_keep_ids(artifacts, daily=daily, weekly=weekly, monthly=monthly)

    deleted = 0
    for artifact in artifacts:
        if str(artifact.id) in keep_ids:
            continue
        with transaction.atomic():
            if artifact.filename:
                with contextlib.suppress(Exception):
                    Path(artifact.filename).unlink(missing_ok=True)
            artifact.delete()
            deleted += 1

    return {"total": len(artifacts), "kept": len(keep_ids), "deleted": deleted}
