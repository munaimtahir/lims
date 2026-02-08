"""
Tests for the accounts app.
"""
import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User


@pytest.fixture
def api_client():
    """Return an API client for making requests."""
    return APIClient()


@pytest.fixture
def admin_user(db):
    """Create and return an admin user."""
    user = User.objects.create_user(
        username="admin",
        email="admin@test.com",
        password="adminpass123",
        full_name="Admin User",
        role="Admin",
    )
    return user


@pytest.fixture
def receptionist_user(db):
    """Create and return a receptionist user."""
    user = User.objects.create_user(
        username="receptionist",
        email="receptionist@test.com",
        password="receppass123",
        full_name="Reception User",
        role="Receptionist",
    )
    return user


@pytest.fixture
def lab_technician_user(db):
    """Create and return a lab technician user."""
    user = User.objects.create_user(
        username="technician",
        email="technician@test.com",
        password="techpass123",
        full_name="Lab Technician User",
        role="Lab Technician",
    )
    return user


@pytest.fixture
def pathologist_user(db):
    """Create and return a pathologist user."""
    user = User.objects.create_user(
        username="pathologist",
        email="pathologist@test.com",
        password="pathopass123",
        full_name="Pathologist User",
        role="Pathologist",
    )
    return user


@pytest.fixture
def manager_user(db):
    """Create and return a manager user."""
    user = User.objects.create_user(
        username="manager",
        email="manager@test.com",
        password="managerpass123",
        full_name="Manager User",
        role="Manager",
    )
    return user


@pytest.fixture
def phlebotomist_user(db):
    """Create and return a phlebotomist user."""
    user = User.objects.create_user(
        username="phlebotomist",
        email="phlebotomist@test.com",
        password="phlebopass123",
        full_name="Phlebotomist User",
        role="Phlebotomist",
    )
    return user


@pytest.fixture
def authenticated_client(api_client, admin_user):
    """Return an authenticated API client with admin user."""
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.mark.django_db
class TestUserModel:
    """Tests for the User model."""

    def test_create_user(self):
        """Test creating a user."""
        user = User.objects.create_user(
            username="testuser",
            email="test@test.com",
            password="testpass123",
            full_name="Test User",
            role="Receptionist",
        )
        assert user.username == "testuser"
        assert user.email == "test@test.com"
        assert user.check_password("testpass123")
        assert user.full_name == "Test User"
        assert user.role == "Receptionist"
        assert user.is_active

    def test_user_role_properties(
        self,
        admin_user,
        receptionist_user,
        lab_technician_user,
        pathologist_user,
        manager_user,
        phlebotomist_user,
    ):
        """Test user role property methods."""
        assert admin_user.is_admin
        assert not admin_user.is_receptionist

        assert receptionist_user.is_receptionist
        assert not receptionist_user.is_admin

        assert lab_technician_user.is_lab_technician
        assert pathologist_user.is_pathologist
        assert manager_user.is_manager
        assert phlebotomist_user.is_phlebotomist

    def test_user_str(self, admin_user):
        """Test user string representation."""
        assert str(admin_user) == "Admin User (Admin)"


@pytest.mark.django_db
class TestLoginView:
    """Tests for the login endpoint."""

    def test_login_with_username(self, api_client, admin_user):
        """Test login with username and password."""
        response = api_client.post(
            "/api/v1/auth/login/", {"username": "admin", "password": "adminpass123"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert "access_token" in response.data["data"]
        assert "refresh_token" in response.data["data"]
        assert response.data["data"]["user"]["username"] == "admin"

    def test_login_with_email(self, api_client, admin_user):
        """Test login with email and password."""
        response = api_client.post(
            "/api/v1/auth/login/",
            {"username": "admin@test.com", "password": "adminpass123"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert response.data["data"]["user"]["email"] == "admin@test.com"

    def test_login_invalid_credentials(self, api_client, admin_user):
        """Test login with invalid credentials."""
        response = api_client.post(
            "/api/v1/auth/login/", {"username": "admin", "password": "wrongpassword"}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_nonexistent_user(self, api_client):
        """Test login with non-existent user."""
        response = api_client.post(
            "/api/v1/auth/login/", {"username": "nonexistent", "password": "password"}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_inactive_user(self, api_client, db):
        """Test login with inactive user."""
        User.objects.create_user(
            username="inactive",
            email="inactive@test.com",
            password="pass123",
            full_name="Inactive User",
            is_active=False,
        )
        response = api_client.post(
            "/api/v1/auth/login/", {"username": "inactive", "password": "pass123"}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestMeView:
    """Tests for the /auth/me endpoint."""

    def test_me_authenticated(self, authenticated_client, admin_user):
        """Test /me endpoint with authenticated user."""
        response = authenticated_client.get("/api/v1/auth/me/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert response.data["data"]["username"] == "admin"
        assert response.data["data"]["role"] == "Admin"

    def test_me_unauthenticated(self, api_client, db):
        """Test /me endpoint without authentication - should return 401."""
        # Make sure no auth headers or credentials
        api_client.credentials()  # Clear any credentials
        response = api_client.get("/api/v1/auth/me/")
        # Should be unauthorized
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestLogoutView:
    """Tests for the logout endpoint."""

    def test_logout(self, authenticated_client):
        """Test logout functionality."""
        response = authenticated_client.post(
            "/api/v1/auth/logout/", {"refresh_token": "some_token"}
        )
        # Even with invalid token, should succeed (just logs warning)
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]


@pytest.mark.django_db
class TestUserViewSet:
    """Tests for the User ViewSet (admin/manager access)."""

    def test_list_users_admin(
        self, authenticated_client, admin_user, receptionist_user
    ):
        """Test listing users as admin."""
        response = authenticated_client.get("/api/v1/auth/users/")
        assert response.status_code == status.HTTP_200_OK

    def test_list_users_non_admin(self, api_client, receptionist_user):
        """Test listing users as non-admin - should be forbidden."""
        api_client.force_authenticate(user=receptionist_user)
        response = api_client.get("/api/v1/auth/users/")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_users_manager(self, api_client, manager_user, receptionist_user):
        """Test listing users as manager."""
        api_client.force_authenticate(user=manager_user)
        response = api_client.get("/api/v1/auth/users/")
        assert response.status_code == status.HTTP_200_OK

    def test_create_user_admin(self, authenticated_client):
        """Test creating a user as admin."""
        response = authenticated_client.post(
            "/api/v1/auth/users/",
            {
                "username": "newuser",
                "email": "newuser@test.com",
                "full_name": "New User",
                "role": "Cashier",
                "password": "newpass123",
                "password_confirm": "newpass123",
            },
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["data"]["username"] == "newuser"

    def test_create_user_manager(self, api_client, manager_user):
        """Test creating a user as manager."""
        api_client.force_authenticate(user=manager_user)
        response = api_client.post(
            "/api/v1/auth/users/",
            {
                "username": "managercreated",
                "email": "managercreated@test.com",
                "full_name": "Manager Created",
                "role": "Receptionist",
                "password": "managerpass123",
                "password_confirm": "managerpass123",
            },
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["data"]["username"] == "managercreated"

    def test_create_user_password_mismatch(self, authenticated_client):
        """Test creating a user with mismatched passwords."""
        response = authenticated_client.post(
            "/api/v1/auth/users/",
            {
                "username": "newuser",
                "email": "newuser@test.com",
                "full_name": "New User",
                "role": "Cashier",
                "password": "newpass123",
                "password_confirm": "differentpass",
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_user_admin(self, authenticated_client, receptionist_user):
        """Test updating a user as admin."""
        response = authenticated_client.patch(
            f"/api/v1/auth/users/{receptionist_user.id}/", {"full_name": "Updated Name"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["data"]["full_name"] == "Updated Name"

    def test_update_user_manager(self, api_client, manager_user, receptionist_user):
        """Test updating a user as manager."""
        api_client.force_authenticate(user=manager_user)
        response = api_client.patch(
            f"/api/v1/auth/users/{receptionist_user.id}/", {"full_name": "Manager Updated"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["data"]["full_name"] == "Manager Updated"

    def test_delete_user_manager(self, api_client, manager_user, receptionist_user):
        """Test deleting a user as manager."""
        api_client.force_authenticate(user=manager_user)
        response = api_client.delete(f"/api/v1/auth/users/{receptionist_user.id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_change_password(self, authenticated_client, admin_user):
        """Test changing user password."""
        response = authenticated_client.post(
            f"/api/v1/auth/users/{admin_user.id}/change_password/",
            {
                "old_password": "adminpass123",
                "new_password": "newadminpass123",
                "new_password_confirm": "newadminpass123",
            },
        )
        assert response.status_code == status.HTTP_200_OK

    def test_change_password_wrong_old(self, authenticated_client, admin_user):
        """Test changing password with wrong old password."""
        response = authenticated_client.post(
            f"/api/v1/auth/users/{admin_user.id}/change_password/",
            {
                "old_password": "wrongold",
                "new_password": "newpass",
                "new_password_confirm": "newpass",
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_reset_password_manager(self, api_client, manager_user, receptionist_user):
        """Test resetting a user's password as manager."""
        api_client.force_authenticate(user=manager_user)
        response = api_client.post(
            f"/api/v1/auth/users/{receptionist_user.id}/reset_password/",
            {
                "new_password": "resetpass123",
                "new_password_confirm": "resetpass123",
            },
        )
        assert response.status_code == status.HTTP_200_OK
