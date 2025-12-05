"""Tests for user authentication and management."""

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


@pytest.mark.django_db
class TestUserModel:
    """Test User model."""

    def test_create_user(self):
        """Test creating a user."""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            role="RECEPTION",
        )
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.role == "RECEPTION"
        assert user.check_password("testpass123")

    def test_user_str(self):
        """Test user string representation."""
        user = User.objects.create_user(
            username="testuser",
            password="testpass123",
            role="ADMIN",
        )
        assert str(user) == "testuser (Admin)"


@pytest.mark.django_db
class TestAuthenticationAPI:
    """Test authentication API endpoints."""

    def setup_method(self):
        """Set up test client and user."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            role="RECEPTION",
        )

    def test_login_success(self):
        """Test successful login."""
        response = self.client.post(
            "/api/auth/login/",
            {"username": "testuser", "password": "testpass123"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data
        assert "user" in response.data
        assert response.data["user"]["role"] == "RECEPTION"
        assert response.data["user"]["username"] == "testuser"

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        response = self.client.post(
            "/api/auth/login/",
            {"username": "testuser", "password": "wrongpassword"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_token_refresh(self):
        """Test token refresh."""
        # Login first
        login_response = self.client.post(
            "/api/auth/login/",
            {"username": "testuser", "password": "testpass123"},
        )
        refresh_token = login_response.data["refresh"]

        # Refresh token
        response = self.client.post(
            "/api/auth/refresh/",
            {"refresh": refresh_token},
        )
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data

    def test_logout(self):
        """Test logout."""
        # Login first
        login_response = self.client.post(
            "/api/auth/login/",
            {"username": "testuser", "password": "testpass123"},
        )
        access_token = login_response.data["access"]
        refresh_token = login_response.data["refresh"]

        # Logout
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        response = self.client.post(
            "/api/auth/logout/",
            {"refresh": refresh_token},
        )
        assert response.status_code == status.HTTP_200_OK

    def test_logout_invalid_token(self):
        """Test logout with invalid token."""
        # Login first
        login_response = self.client.post(
            "/api/auth/login/",
            {"username": "testuser", "password": "testpass123"},
        )
        access_token = login_response.data["access"]

        # Logout with invalid refresh token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        response = self.client.post(
            "/api/auth/logout/",
            {"refresh": "invalid_token"},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
