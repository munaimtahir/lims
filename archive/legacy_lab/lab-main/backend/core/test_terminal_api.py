"""Tests for terminal management API."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from core.models import LabTerminal

User = get_user_model()


class TerminalManagementAPITestCase(TestCase):
    """Test terminal management API endpoints."""

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
            username="user",
            email="user@example.com",
            password="user123",
            role="RECEPTION",
        )
        self.terminal1 = LabTerminal.objects.create(
            code="LAB1-PC",
            name="Lab 1 PC",
            offline_range_start=1000,
            offline_range_end=1999,
        )

    def test_list_terminals_as_admin(self):
        """Test listing terminals as admin."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get("/api/terminals/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertGreaterEqual(len(response.data["results"]), 1)

    def test_list_terminals_as_non_admin(self):
        """Test listing terminals as non-admin is forbidden."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get("/api/terminals/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_terminal_as_admin(self):
        """Test creating a terminal as admin."""
        self.client.force_authenticate(user=self.admin_user)
        data = {
            "code": "LAB2-PC",
            "name": "Lab 2 PC",
            "offline_range_start": 2000,
            "offline_range_end": 2999,
            "is_active": True,
        }
        response = self.client.post("/api/terminals/", data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(LabTerminal.objects.count(), 2)

    def test_update_terminal_as_admin(self):
        """Test updating a terminal as admin."""
        self.client.force_authenticate(user=self.admin_user)
        data = {"name": "Lab 1 PC Updated"}
        response = self.client.patch(f"/api/terminals/{self.terminal1.id}/", data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.terminal1.refresh_from_db()
        self.assertEqual(self.terminal1.name, "Lab 1 PC Updated")

    def test_delete_terminal_as_admin(self):
        """Test deleting a terminal as admin."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(f"/api/terminals/{self.terminal1.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(LabTerminal.objects.count(), 0)

    def test_validate_range_order(self):
        """Test that start must be less than end."""
        self.client.force_authenticate(user=self.admin_user)
        data = {
            "code": "INVALID",
            "name": "Invalid Terminal",
            "offline_range_start": 3000,
            "offline_range_end": 2000,
        }
        response = self.client.post("/api/terminals/", data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("offline_range_start", response.data["error"]["details"])

    def test_validate_no_overlap(self):
        """Test that ranges cannot overlap."""
        self.client.force_authenticate(user=self.admin_user)
        # Create overlapping range
        data = {
            "code": "LAB3-PC",
            "name": "Lab 3 PC",
            "offline_range_start": 1500,  # Overlaps with terminal1
            "offline_range_end": 2500,
        }
        response = self.client.post("/api/terminals/", data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_terminal_no_overlap(self):
        """Test updating terminal validates no overlap."""
        self.client.force_authenticate(user=self.admin_user)
        terminal2 = LabTerminal.objects.create(
            code="LAB2-PC",
            name="Lab 2 PC",
            offline_range_start=2000,
            offline_range_end=2999,
        )
        # Try to update terminal2 to overlap with terminal1
        data = {
            "offline_range_start": 1500,
            "offline_range_end": 2500,
        }
        response = self.client.patch(f"/api/terminals/{terminal2.id}/", data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_code_format_validation(self):
        """Test code format validation."""
        self.client.force_authenticate(user=self.admin_user)
        data = {
            "code": "INV@LID",
            "name": "Invalid Terminal",
            "offline_range_start": 3000,
            "offline_range_end": 3999,
        }
        response = self.client.post("/api/terminals/", data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("code", response.data["error"]["details"])

    def test_code_converted_to_uppercase(self):
        """Test that code is converted to uppercase."""
        self.client.force_authenticate(user=self.admin_user)
        data = {
            "code": "lab3-pc",
            "name": "Lab 3 PC",
            "offline_range_start": 3000,
            "offline_range_end": 3999,
        }
        response = self.client.post("/api/terminals/", data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        terminal = LabTerminal.objects.get(id=response.data["id"])
        self.assertEqual(terminal.code, "LAB3-PC")
