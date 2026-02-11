"""
Serializers for User authentication and management.
"""

from django.contrib.auth import authenticate
from rest_framework import serializers

from apps.core.models import Branch
from .models import User, UserBranchMembership



class BranchSerializer(serializers.ModelSerializer):
    """Serializer for Branch details."""
    
    class Meta:
        model = Branch
        fields = ["id", "code", "name", "capability_mode", "is_hq", "is_active"]


class UserBranchMembershipSerializer(serializers.ModelSerializer):
    """Serializer for User-Branch membership."""
    
    branch = BranchSerializer(read_only=True)
    
    class Meta:
        model = UserBranchMembership
        fields = ["branch", "role", "is_active"]


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the User model.

    Serializes all essential user fields for display.
    """
    
    branch_memberships = UserBranchMembershipSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "full_name",
            "role",
            "is_active",
            "date_joined",
            "last_login",
            "branch_memberships",
        ]
        read_only_fields = ["id", "date_joined", "last_login"]


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new user accounts.

    Includes password confirmation and handles user creation.
    """

    password = serializers.CharField(
        write_only=True, required=True, style={"input_type": "password"}
    )
    password_confirm = serializers.CharField(
        write_only=True, required=True, style={"input_type": "password"}
    )

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "full_name",
            "role",
            "password",
            "password_confirm",
        ]

    def validate(self, attrs):
        """
        Validate that the password and password_confirm fields match.

        Args:
            attrs (dict): The dictionary of attributes to validate.

        Returns:
            dict: The validated attributes.

        Raises:
            serializers.ValidationError: If the passwords do not match.
        """
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password": "Password fields didn't match."}
            )
        return attrs

    def create(self, validated_data):
        """
        Create a new user with the validated data.

        The 'password_confirm' field is removed, and the 'password' is hashed
        before creating the user.

        Args:
            validated_data (dict): The data to create the user with.

        Returns:
            User: The newly created user instance.
        """
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")
        user = User.objects.create_user(**validated_data, password=password)
        return user


class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login.

    Supports login via username or email.
    Validates user credentials and authenticates the user.
    """

    username = serializers.CharField(required=True)
    password = serializers.CharField(
        required=True, write_only=True, style={"input_type": "password"}
    )

    def validate(self, attrs):
        """
        Validate the username/email and password for authentication.

        Supports login with either username or email address.

        Args:
            attrs (dict): The dictionary of attributes to validate.

        Returns:
            dict: The validated attributes with the user instance.

        Raises:
            serializers.ValidationError: If authentication fails or the user is inactive.
        """
        username_or_email = attrs.get("username")
        password = attrs.get("password")

        if username_or_email and password:
            # Check if input is an email
            if "@" in username_or_email:
                try:
                    user_obj = User.objects.get(email=username_or_email)
                    username = user_obj.username
                except User.DoesNotExist:
                    # Use generic message to prevent user enumeration
                    raise serializers.ValidationError("Invalid credentials.")
            else:
                username = username_or_email

            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError("Invalid credentials.")
            if not user.is_active:
                raise serializers.ValidationError("User account is disabled.")
        else:
            raise serializers.ValidationError('Must include "username" and "password".')

        attrs["user"] = user
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for changing a user's password.
    """

    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)
    new_password_confirm = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        """
        Validate that the new password and confirmation match.

        Args:
            attrs (dict): The dictionary of attributes to validate.

        Returns:
            dict: The validated attributes.

        Raises:
            serializers.ValidationError: If the new passwords do not match.
        """
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password": "New password fields didn't match."}
            )
        return attrs


class ResetPasswordSerializer(serializers.Serializer):
    """
    Serializer for resetting a user's password by an admin/manager.
    """

    new_password = serializers.CharField(required=True, write_only=True)
    new_password_confirm = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        """
        Validate that the new password and confirmation match.

        Args:
            attrs (dict): The dictionary of attributes to validate.

        Returns:
            dict: The validated attributes.

        Raises:
            serializers.ValidationError: If the new passwords do not match.
        """
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password": "New password fields didn't match."}
            )
        return attrs
