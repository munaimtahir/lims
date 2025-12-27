"""Tests for catalog management API."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from catalog.models import TestCatalog

User = get_user_model()


class CatalogManagementAPITestCase(TestCase):
    """Test catalog management API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.admin_user = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="admin123",
            role="ADMIN",
        )
        self.regular_user = User.objects.create_user(
            username="tech",
            email="tech@example.com",
            password="tech123",
            role="TECHNOLOGIST",
        )
        self.test1 = TestCatalog.objects.create(
            code="CBC",
            name="Complete Blood Count",
            category="Hematology",
            sample_type="Blood",
            price=500.00,
            turnaround_time_hours=24,
        )

    def test_list_tests_authenticated(self):
        """Test listing tests as authenticated user."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get("/api/catalog/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertGreaterEqual(len(response.data["results"]), 1)

    def test_create_test_as_admin(self):
        """Test creating a test as admin."""
        self.client.force_authenticate(user=self.admin_user)
        data = {
            "code": "LFT",
            "name": "Liver Function Test",
            "category": "Chemistry",
            "sample_type": "Serum",
            "price": 800.00,
            "turnaround_time_hours": 48,
            "is_active": True,
        }
        response = self.client.post("/api/catalog/", data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TestCatalog.objects.count(), 2)

    def test_create_test_as_non_admin(self):
        """Test creating a test as non-admin is forbidden."""
        self.client.force_authenticate(user=self.regular_user)
        data = {
            "code": "RFT",
            "name": "Renal Function Test",
            "category": "Chemistry",
            "sample_type": "Serum",
            "price": 700.00,
            "turnaround_time_hours": 48,
        }
        response = self.client.post("/api/catalog/", data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_test_as_admin(self):
        """Test updating a test as admin."""
        self.client.force_authenticate(user=self.admin_user)
        data = {"price": 600.00, "name": "Complete Blood Count (Updated)"}
        response = self.client.patch(f"/api/catalog/{self.test1.id}/", data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.test1.refresh_from_db()
        self.assertEqual(self.test1.price, 600.00)

    def test_delete_test_as_admin(self):
        """Test deleting a test as admin."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(f"/api/catalog/{self.test1.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(TestCatalog.objects.count(), 0)

    def test_validate_price_positive(self):
        """Test that price must be positive."""
        self.client.force_authenticate(user=self.admin_user)
        data = {
            "code": "INVALID",
            "name": "Invalid Test",
            "category": "Test",
            "sample_type": "Blood",
            "price": -100.00,
            "turnaround_time_hours": 24,
        }
        response = self.client.post("/api/catalog/", data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("price", response.data["error"]["details"])

    def test_validate_code_format(self):
        """Test that code must be alphanumeric."""
        self.client.force_authenticate(user=self.admin_user)
        data = {
            "code": "IN@VALID",
            "name": "Invalid Test",
            "category": "Test",
            "sample_type": "Blood",
            "price": 100.00,
            "turnaround_time_hours": 24,
        }
        response = self.client.post("/api/catalog/", data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("code", response.data["error"]["details"])

    def test_code_converted_to_uppercase(self):
        """Test that code is converted to uppercase."""
        self.client.force_authenticate(user=self.admin_user)
        data = {
            "code": "test",
            "name": "Test",
            "category": "Test",
            "sample_type": "Blood",
            "price": 100.00,
            "turnaround_time_hours": 24,
        }
        response = self.client.post("/api/catalog/", data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        test = TestCatalog.objects.get(id=response.data["id"])
        self.assertEqual(test.code, "TEST")
