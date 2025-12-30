"""Views for settings app."""

from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import RolePermission, WorkflowSettings
from .serializers import RolePermissionSerializer, WorkflowSettingsSerializer


class WorkflowSettingsView(APIView):
    """
    Manages the singleton WorkflowSettings object.

    Provides endpoints for retrieving and updating the workflow settings.
    """

    def get(self, request):
        """
        Retrieves the current workflow settings.

        Args:
            request: The request object.

        Returns:
            Response: A response object with the workflow settings data.
        """
        settings = WorkflowSettings.load()
        serializer = WorkflowSettingsSerializer(settings)
        return Response(serializer.data)

    def put(self, request):
        """
        Updates the workflow settings.

        Args:
            request: The request object with the new settings data.

        Returns:
            Response: A response object with the updated settings or an error message.
        """
        settings = WorkflowSettings.load()
        serializer = WorkflowSettingsSerializer(settings, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RolePermissionListView(generics.ListAPIView):
    """
    Lists all role permissions.
    """

    queryset = RolePermission.objects.all()
    serializer_class = RolePermissionSerializer


class RolePermissionUpdateView(APIView):
    """
    Performs a bulk update of role permissions.

    Accepts a list of role permission objects and updates them accordingly.
    """

    def put(self, request):
        """
        Handles the bulk update of role permissions.

        Args:
            request: The request object, containing a list of permissions data.

        Returns:
            Response: A response object with the updated permissions
            or an error message.
        """
        permissions_data = request.data
        if not isinstance(permissions_data, list):
            return Response(
                {"error": "Expected a list of permissions"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        updated_permissions = []
        for perm_data in permissions_data:
            role = perm_data.get("role")
            if not role:
                continue

            permission, created = RolePermission.objects.get_or_create(role=role)
            serializer = RolePermissionSerializer(
                permission, data=perm_data, partial=True
            )
            if serializer.is_valid():
                serializer.save()
                updated_permissions.append(serializer.data)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response(updated_permissions)


# Import from permissions module to maintain single source of truth
from .permissions import TEMPORARY_FULL_ACCESS_MODE


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_user_permissions(request):
    """
    Retrieves the permissions for the currently authenticated user.

    The permissions are determined by the user's role.

    Args:
        request: The request object.

    Returns:
        Response: A response object containing the user's role and permissions.
    """
    user = request.user

    default_perms = {
        "can_register": False,
        "can_collect": False,
        "can_enter_result": False,
        "can_verify": False,
        "can_publish": False,
        "can_edit_catalog": False,
        "can_edit_settings": False,
    }

    # TEMPORARY FULL PERMISSION OVERRIDE — REMOVE LATER WHEN FINE-GRAINED PERMISSIONS ARE ACTIVATED.
    if TEMPORARY_FULL_ACCESS_MODE:
        default_perms = dict.fromkeys(default_perms, True)
    elif user.role == "ADMIN":
        default_perms = dict.fromkeys(default_perms, True)
    else:
        try:
            role_perm = RolePermission.objects.get(role=user.role)
            default_perms = {
                "can_register": role_perm.can_register,
                "can_collect": role_perm.can_collect,
                "can_enter_result": role_perm.can_enter_result,
                "can_verify": role_perm.can_verify,
                "can_publish": role_perm.can_publish,
                "can_edit_catalog": role_perm.can_edit_catalog,
                "can_edit_settings": role_perm.can_edit_settings,
            }
        except RolePermission.DoesNotExist:
            pass

    return Response(
        {
            "role": user.role,
            "permissions": default_perms,
        }
    )
