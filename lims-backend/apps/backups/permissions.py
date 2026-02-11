from rest_framework.permissions import BasePermission


class BackupPermission(BasePermission):
    """Action-level permission mapping for backup endpoints."""

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True

        action = getattr(view, "action", None)
        method = request.method.upper()
        role = getattr(user, "role", "")
        is_operator = role in {"Admin", "Manager", "Pathologist"}

        if method == "GET":
            if action == "download":
                return user.has_perm("backups.can_download_backup") or is_operator
            return (
                user.has_perm("backups.can_download_backup")
                or user.has_perm("backups.can_create_backup")
                or is_operator
            )

        if action in {"create", "import_backup", "push", "offsite_test"}:
            return user.has_perm("backups.can_create_backup") or is_operator
        if action == "restore":
            return user.has_perm("backups.can_restore_backup") or is_operator
        if action == "destroy":
            return user.has_perm("backups.can_delete_backup") or role in {"Admin", "Manager"}
        return False
