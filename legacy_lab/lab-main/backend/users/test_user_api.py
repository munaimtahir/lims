"""Tests for user management API."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


class UserManagementAPITestCase(TestCase):
    """Test user management API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.admin_user = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="admin123",
            role="ADMIN",
            first_name="Admin",
            last_name="User",
        )
        self.regular_user = User.objects.create_user(
            username="user1",
            email="user1@example.com",
            password="user123",
            role="RECEPTION",
            first_name="Regular",
            last_name="User",
        )

    def test_list_users_as_admin(self):
        """Test listing users as admin."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get("/api/auth/users/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertGreaterEqual(len(response.data["results"]), 2)

    def test_list_users_as_non_admin(self):
        """Test listing users as non-admin is forbidden."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get("/api/auth/users/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_user_as_admin(self):
        """Test creating a user as admin."""
        self.client.force_authenticate(user=self.admin_user)
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "newpass123",
            "role": "TECHNOLOGIST",
            "first_name": "New",
            "last_name": "User",
            "is_active": True,
        }
        response = self.client.post("/api/auth/users/", data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 3)
        new_user = User.objects.get(username="newuser")
        self.assertTrue(new_user.check_password("newpass123"))

    def test_update_user_as_admin(self):
        """Test updating a user as admin."""
        self.client.force_authenticate(user=self.admin_user)
        data = {
            "first_name": "Updated",
            "last_name": "Name",
            "email": "updated@example.com",
        }
        response = self.client.patch(f"/api/auth/users/{self.regular_user.id}/", data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.regular_user.refresh_from_db()
        self.assertEqual(self.regular_user.first_name, "Updated")
        self.assertEqual(self.regular_user.email, "updated@example.com")

    def test_soft_delete_user(self):
        """Test soft deleting a user."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(f"/api/auth/users/{self.regular_user.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.regular_user.refresh_from_db()
        self.assertFalse(self.regular_user.is_active)
        # User still exists in database
        self.assertEqual(User.objects.count(), 2)

    def test_create_user_without_password(self):
        """Test creating a user without password sets unusable password."""
        self.client.force_authenticate(user=self.admin_user)
        data = {
            "username": "nopassuser",
            "email": "nopass@example.com",
            "role": "RECEPTION",
            "first_name": "No",
            "last_name": "Pass",
            "is_active": True,
        }
        response = self.client.post("/api/auth/users/", data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        new_user = User.objects.get(username="nopassuser")
        self.assertFalse(new_user.has_usable_password())

    def test_update_user_password(self):
        """Test updating user password."""
        self.client.force_authenticate(user=self.admin_user)
        data = {"password": "newpassword123"}
        response = self.client.patch(f"/api/auth/users/{self.regular_user.id}/", data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.regular_user.refresh_from_db()
        self.assertTrue(self.regular_user.check_password("newpassword123"))
