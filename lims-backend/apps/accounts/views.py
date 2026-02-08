"""
API views for user authentication and management.
"""

from django.contrib.auth import logout
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .permissions import IsManagerOrAdmin
from .serializers import (
    ChangePasswordSerializer,
    LoginSerializer,
    ResetPasswordSerializer,
    UserCreateSerializer,
    UserSerializer,
)


class AuthViewSet(viewsets.GenericViewSet):
    """
    ViewSet for handling user authentication.

    Provides `login`, `logout`, and `me` endpoints.
    """

    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def get_permissions(self):
        """
        Return the appropriate permissions based on the action.

        - login: AllowAny
        - logout, me: IsAuthenticated
        """
        if self.action in ["logout", "me"]:
            return [IsAuthenticated()]
        return [AllowAny()]

    @action(detail=False, methods=["post"])
    def login(self, request):
        """
        Authenticate a user and return JWT tokens.

        Args:
            request (Request): The request object containing username and password.

        Returns:
            Response: A response object with user data, access token, and refresh token.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "success": True,
                "data": {
                    "user": UserSerializer(user).data,
                    "access_token": str(refresh.access_token),
                    "refresh_token": str(refresh),
                },
                "message": "Login successful",
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def logout(self, request):
        """
        Log out a user by blacklisting their refresh token.

        Args:
            request (Request): The request object containing the refresh token.

        Returns:
            Response: A success or failure message.
        """
        try:
            refresh_token = request.data.get("refresh_token")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            logout(request)
            return Response(
                {"success": True, "message": "Logout successful"},
                status=status.HTTP_200_OK,
            )
        except Exception:
            return Response(
                {"success": False, "message": "Invalid token"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def me(self, request):
        """
        Retrieve the profile of the currently authenticated user.

        Args:
            request (Request): The request object.

        Returns:
            Response: A response object with the current user's data.
        """
        return Response(
            {"success": True, "data": UserSerializer(request.user).data},
            status=status.HTTP_200_OK,
        )


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for User CRUD operations.

    This ViewSet is restricted to admin and manager users. It allows for creating,
    retrieving, updating, and deleting users.
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsManagerOrAdmin]
    filterset_fields = ["role", "is_active"]
    search_fields = ["username", "email", "full_name"]
    ordering_fields = ["date_joined", "username"]

    def get_serializer_class(self):
        """
        Return the appropriate serializer class based on the request action.

        - For `create` action, `UserCreateSerializer` is used.
        - For all other actions, `UserSerializer` is used.

        Returns:
            Serializer: The serializer class for the current action.
        """
        if self.action == "create":
            return UserCreateSerializer
        return UserSerializer

    def create(self, request, *args, **kwargs):
        """
        Create a new user.

        Args:
            request (Request): The request object containing user data.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Response: A response object with the created user data.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response(
            {
                "success": True,
                "data": UserSerializer(user).data,
                "message": "User created successfully",
            },
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        """
        Update a user's details.

        Args:
            request (Request): The request object with the updated data.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments containing the user's primary key.

        Returns:
            Response: A response object with the updated user data.
        """
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response(
            {
                "success": True,
                "data": UserSerializer(user).data,
                "message": "User updated successfully",
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"])
    def change_password(self, request, pk=None):
        """
        Change a user's password.

        Args:
            request (Request): The request object containing old and new passwords.
            pk (int, optional): The primary key of the user. Defaults to None.

        Returns:
            Response: A success or failure message.
        """
        user = self.get_object()
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Check old password
        if not user.check_password(serializer.validated_data["old_password"]):
            return Response(
                {"success": False, "message": "Old password is incorrect"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Set new password
        user.set_password(serializer.validated_data["new_password"])
        user.save()

        return Response(
            {"success": True, "message": "Password changed successfully"},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"])
    def reset_password(self, request, pk=None):
        """
        Reset a user's password (admin/manager action).

        Args:
            request (Request): The request object containing new password fields.
            pk (int, optional): The primary key of the user. Defaults to None.

        Returns:
            Response: A success or failure message.
        """
        user = self.get_object()
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user.set_password(serializer.validated_data["new_password"])
        user.save()

        return Response(
            {"success": True, "message": "Password reset successfully"},
            status=status.HTTP_200_OK,
        )
