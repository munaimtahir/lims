"""Tests for catalog app."""

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from .models import TestCatalog

User = get_user_model()


@pytest.mark.django_db
class TestCatalogAPI:
    """Test catalog API endpoints."""

    def setup_method(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
            role="RECEPTION",
        )
        self.test1 = TestCatalog.objects.create(
            code="CBC",
            name="Complete Blood Count",
            category="Hematology",
            sample_type="Blood",
            price=500.00,
            turnaround_time_hours=24,
        )
        self.test2 = TestCatalog.objects.create(
            code="LFT",
            name="Liver Function Test",
            category="Biochemistry",
            sample_type="Blood",
            price=800.00,
            turnaround_time_hours=48,
        )

    def test_list_catalog(self):
        """Test listing test catalog."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/catalog/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2

    def test_get_catalog_detail(self):
        """Test getting catalog detail."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f"/api/catalog/{self.test1.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["code"] == "CBC"

    def test_list_catalog_unauthenticated(self):
        """Test that unauthenticated users cannot list catalog."""
        response = self.client.get("/api/catalog/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
