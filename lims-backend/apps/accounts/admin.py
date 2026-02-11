"""
Django admin configuration for accounts app.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User, UserBranchMembership


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Admin configuration for custom User model.
    """

    list_display = [
        "username",
        "email",
        "full_name",
        "role",
        "tenant",
        "is_active",
        "date_joined",
    ]
    list_filter = ["role", "is_active", "is_staff", "date_joined"]
    search_fields = ["username", "email", "full_name"]
    ordering = ["-date_joined"]

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal info", {"fields": ("full_name", "email", "tenant")}),
        (
            "Permissions",
            {
                "fields": (
                    "role",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "email",
                    "full_name",
                    "role",
                    "password1",
                    "password2",
                ),
            },
        ),
    )


@admin.register(UserBranchMembership)
class UserBranchMembershipAdmin(admin.ModelAdmin):
    list_display = ["user", "branch", "role", "is_active", "updated_at"]
    list_filter = ["role", "is_active", "branch__tenant"]
    search_fields = ["user__username", "user__full_name", "branch__name", "branch__code"]
    autocomplete_fields = ["user", "branch"]
