"""Views for user authentication and management."""

from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from core.permissions import IsAdminUser

from .models import User
from .serializers import (
    CustomTokenObtainPairSerializer,
    UserCreateUpdateSerializer,
    UserSerializer,
)


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom login view that includes user role information in the token response.
    """

    serializer_class = CustomTokenObtainPairSerializer


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """
    Logs a user out by blacklisting their refresh token.

    Args:
        request: The request object, containing the refresh token.

    Returns:
        Response: A response object with a success or error message.
    """
    try:
        refresh_token = request.data.get("refresh")
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        return Response(
            {"detail": "Successfully logged out."}, status=status.HTTP_200_OK
        )
    except Exception:
        return Response(
            {"detail": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST
        )


class UserListCreateView(generics.ListCreateAPIView):
    """
    Lists and creates users.

    Access is restricted to admin users.
    """

    queryset = User.objects.all().order_by("id")
    permission_classes = [IsAdminUser]

    def get_serializer_class(self):
        """
        Returns the appropriate serializer class based on the request method.
        """
        if self.request.method == "POST":
            return UserCreateUpdateSerializer
        return UserSerializer


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieves, updates, and soft-deletes a specific user.

    Access is restricted to admin users. Deleting a user deactivates their
    account instead of permanently removing it.
    """

    queryset = User.objects.all()
    permission_classes = [IsAdminUser]

    def get_serializer_class(self):
        """
        Returns the appropriate serializer class based on the request method.
        """
        if self.request.method in ["PUT", "PATCH"]:
            return UserCreateUpdateSerializer
        return UserSerializer

    def perform_destroy(self, instance):
        """
        Performs a soft delete by deactivating the user account.

        Args:
            instance (User): The user instance to deactivate.
        """
        instance.is_active = False
        instance.save()
