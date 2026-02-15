"""
Unit tests for file-storage settings (no DB required).
Ensures MEDIA_URL, MEDIA_ROOT, and UPLOADS_ROOT are set correctly for production wiring.
"""
import pytest
from django.conf import settings


class TestStorageSettings:
    """Assert file-storage settings match Caddy and Docker mount paths."""

    def test_media_url(self):
        assert settings.MEDIA_URL == "/media/"

    def test_media_root(self):
        # In container: /app/media; locally may be path under BASE_DIR
        assert settings.MEDIA_ROOT is not None
        media = str(settings.MEDIA_ROOT)
        assert media.endswith("/media") or media == "/app/media"

    def test_uploads_root_default(self):
        assert getattr(settings, "UPLOADS_ROOT", None) is not None
        assert settings.UPLOADS_ROOT == "/app/uploads" or settings.UPLOADS_ROOT.endswith(
            "uploads"
        )
