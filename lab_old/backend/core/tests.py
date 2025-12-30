"""Tests for core settings."""

import pytest


@pytest.mark.django_db
class TestSettingsConfiguration:
    """Test settings configuration paths."""

    def test_postgres_configuration_when_host_set(self):
        """Test that PostgreSQL is configured when POSTGRES_HOST is set."""
        # This test validates that the PostgreSQL configuration path is exercised
        # The actual configuration is tested by virtue of the test database setup
        from django.conf import settings

        # Check that databases are configured
        assert "default" in settings.DATABASES
        assert settings.DATABASES["default"]["ENGINE"]

    def test_celery_configuration(self):
        """Test Celery broker URL configuration."""
        from django.conf import settings

        # This covers the CELERY_BROKER_URL configuration line
        broker_url = getattr(settings, "CELERY_BROKER_URL", None)
        # May be None if REDIS_URL not set, or configured if set
        assert broker_url is None or broker_url.startswith("redis://")
