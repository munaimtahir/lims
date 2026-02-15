"""
Serializers for the Patient model.
"""

import calendar
from datetime import date, timedelta

from rest_framework import serializers

from apps.core.models import Branch, CollectionCenter
from apps.core.authz import user_tenant
from apps.core.services.settings import get_tenant_settings

from .models import Patient


def calculate_age_parts(dob, today=None):
    """Calculate age in years, months, and days from date of birth."""
    if not dob:
        return None, None, None
    today = today or date.today()
    years = today.year - dob.year
    months = today.month - dob.month
    days = today.day - dob.day

    if days < 0:
        prev_month = today.month - 1 or 12
        prev_year = today.year if today.month > 1 else today.year - 1
        days += calendar.monthrange(prev_year, prev_month)[1]
        months -= 1

    if months < 0:
        months += 12
        years -= 1

    return years, months, days


def calculate_dob_from_age(years, months=0, days=0, today=None):
    """Calculate date of birth from age components."""
    if years is None:
        return None
    today = today or date.today()
    year = today.year - years
    month = today.month - (months or 0)
    while month <= 0:
        year -= 1
        month += 12
    day = min(today.day, calendar.monthrange(year, month)[1])
    dob = date(year, month, day)
    if days:
        dob -= timedelta(days=days)
    return dob


class PatientValidationMixin:
    """
    Mixin for shared patient validation logic across serializers.

    Validates required fields and DOB/age consistency with ±1 day tolerance.
    The tolerance accounts for timezone differences, month-end edge cases,
    and leap year variations in age calculations.
    """

    def validate_patient_data(self, attrs, instance=None):
        """
        Validate patient data for required fields and DOB/age rules.

        Args:
            attrs: Validated data attributes
            instance: Existing patient instance (for updates)

        Returns:
            Validated and potentially modified attributes

        Raises:
            serializers.ValidationError: If validation fails
        """
        dob = attrs.get(
            "date_of_birth",
            getattr(instance, "date_of_birth", None) if instance else None,
        )
        age_years = attrs.get(
            "age_years", getattr(instance, "age_years", None) if instance else None
        )
        age_months = (
            attrs.get(
                "age_months",
                getattr(instance, "age_months", None) if instance else None,
            )
            or 0
        )
        age_days = (
            attrs.get(
                "age_days", getattr(instance, "age_days", None) if instance else None
            )
            or 0
        )
        first_name = attrs.get(
            "first_name", getattr(instance, "first_name", None) if instance else None
        )
        last_name = attrs.get(
            "last_name", getattr(instance, "last_name", None) if instance else None
        )
        full_name = attrs.get(
            "full_name", getattr(instance, "full_name", None) if instance else None
        )
        phone = attrs.get(
            "phone", getattr(instance, "phone", None) if instance else None
        )
        gender = attrs.get(
            "gender", getattr(instance, "gender", None) if instance else None
        )

        if not phone:
            raise serializers.ValidationError({"phone": "Mobile number is required."})
        if not gender:
            raise serializers.ValidationError({"gender": "Gender is required."})
        if not full_name and not (first_name or last_name):
            raise serializers.ValidationError(
                {"full_name": "Patient name is required."}
            )

        if dob is None and age_years is None:
            raise serializers.ValidationError(
                {"date_of_birth": "Provide date of birth or age in years."}
            )

        # Validate DOB and age consistency with ±1 day tolerance
        # Tolerance accounts for timezone differences, leap years, and month-end edge cases
        if dob and age_years is not None:
            expected_dob = calculate_dob_from_age(age_years, age_months, age_days)
            if expected_dob and abs((dob - expected_dob).days) > 1:
                raise serializers.ValidationError(
                    {"date_of_birth": "Date of birth does not match provided age."}
                )

        # Auto-calculate age from DOB if not provided
        if dob and age_years is None:
            years, months, days = calculate_age_parts(dob)
            attrs["age_years"] = years
            attrs["age_months"] = months
            attrs["age_days"] = days

        return attrs


class PatientSerializer(PatientValidationMixin, serializers.ModelSerializer):
    """
    Serializer for the Patient model.

    Includes all patient fields and computed properties like age, full_name,
    total_orders, and last_visit. Used for detailed patient views.
    """

    age = serializers.ReadOnlyField()
    full_name = serializers.SerializerMethodField()
    total_orders = serializers.ReadOnlyField()
    last_visit = serializers.ReadOnlyField()

    class Meta:
        model = Patient
        fields = [
            "id",
            "patient_id",
            "first_name",
            "last_name",
            "full_name",
            "date_of_birth",
            "age_years",
            "age_months",
            "age_days",
            "age",
            "gender",
            "phone",
            "whatsapp_number",
            "email",
            "national_id",
            "address",
            "cnic",
            "father_husband_name",
            "default_referred_by",
            "registration_number",
            "registration_center",
            "registration_datetime",
            "created_at",
            "updated_at",
            "total_orders",
            "last_visit",
        ]
        read_only_fields = [
            "id",
            "patient_id",
            "registration_number",
            "registration_datetime",
            "created_at",
            "updated_at",
        ]

    def get_full_name(self, obj):
        """
        Return the patient's full name.

        Args:
            obj (Patient): The patient instance.

        Returns:
            str: The concatenated first and last name.
        """
        return obj.get_full_name()

    def validate_phone(self, value):
        """
        Validate the phone number format.

        Ensures the phone number is not empty and has a minimum length.

        Args:
            value (str): The phone number to validate.

        Returns:
            str: The validated phone number.

        Raises:
            serializers.ValidationError: If the phone number is invalid.
        """
        if not value:
            raise serializers.ValidationError("Phone number is required.")
        if len(value) < 10:
            raise serializers.ValidationError(
                "Phone number must be at least 10 digits."
            )
        return value

    def validate_date_of_birth(self, value):
        """
        Validate that the date of birth is not in the future.

        Args:
            value (date): The date of birth to validate.

        Returns:
            date: The validated date of birth.

        Raises:
            serializers.ValidationError: If the date of birth is in the future.
        """
        if value > date.today():
            raise serializers.ValidationError("Date of birth cannot be in the future.")
        return value

    def validate(self, attrs):
        """Validate patient data for required fields and DOB/age rules."""
        return self.validate_patient_data(
            attrs, instance=getattr(self, "instance", None)
        )


class PatientCreateSerializer(PatientValidationMixin, serializers.ModelSerializer):
    """
    Serializer for creating new patient records.

    This serializer includes only the fields required for creating a new patient.
    Collection center is optional (feature flag). When OFF, registration_center
    is ignored if invalid; when ON, center can be resolved from branch or default.
    """

    branch = serializers.IntegerField(
        required=False,
        allow_null=True,
        write_only=True,
        help_text="Branch id (preferred when enable_collection_centers=True); maps to registration_center by code.",
    )

    class Meta:
        model = Patient
        fields = [
            "first_name",
            "last_name",
            "full_name",
            "date_of_birth",
            "age_years",
            "age_months",
            "age_days",
            "gender",
            "phone",
            "whatsapp_number",
            "email",
            "national_id",
            "cnic",
            "father_husband_name",
            "default_referred_by",
            "address",
            "registration_center",
            "branch",
        ]

    def validate_phone(self, value):
        """
        Validate the phone number format.

        Ensures the phone number is not empty and has a minimum length.

        Args:
            value (str): The phone number to validate.

        Returns:
            str: The validated phone number.

        Raises:
            serializers.ValidationError: If the phone number is invalid.
        """
        if not value:
            raise serializers.ValidationError("Phone number is required.")
        if len(value) < 10:
            raise serializers.ValidationError(
                "Phone number must be at least 10 digits."
            )
        return value

    def validate_date_of_birth(self, value):
        """
        Validate that the date of birth is not in the future.

        Args:
            value (date): The date of birth to validate.

        Returns:
            date: The validated date of birth.

        Raises:
            serializers.ValidationError: If the date of birth is in the future.
        """
        if value > date.today():
            raise serializers.ValidationError("Date of birth cannot be in the future.")
        return value

    def _get_tenant_settings(self):
        request = self.context.get("request")
        if not request or not getattr(request, "user", None):
            return None
        tenant = user_tenant(request.user)
        return get_tenant_settings(tenant)

    def validate(self, attrs):
        """Validate patient data and resolve registration_center from tenant settings and payload."""
        attrs = self.validate_patient_data(attrs, instance=None)
        tenant_settings = self._get_tenant_settings()
        enable_cc = tenant_settings.enable_collection_centers if tenant_settings else False

        # Resolve branch from write-only field (preferred when centers ON)
        branch_id = attrs.pop("branch", None)
        reg_center = attrs.get("registration_center")

        if enable_cc:
            # Collection centers ON: accept (1) valid CC pk, (2) branch id in branch field,
            # (3) registration_center that is actually a Branch pk (compatibility bridge).
            resolved_center = None
            if reg_center is not None:
                try:
                    resolved_center = CollectionCenter.objects.get(pk=reg_center)
                except (CollectionCenter.DoesNotExist, TypeError):
                    branch = Branch.objects.filter(pk=reg_center).first()
                    if branch:
                        # Compatibility bridge: remove after UI migration, gated by enable_collection_centers.
                        center, _ = CollectionCenter.objects.get_or_create(
                            code=branch.code,
                            defaults={"name": branch.name, "is_active": True},
                        )
                        resolved_center = center
            if resolved_center is None and branch_id is not None:
                branch = Branch.objects.filter(pk=branch_id).first()
                if branch:
                    center, _ = CollectionCenter.objects.get_or_create(
                        code=branch.code,
                        defaults={"name": branch.name, "is_active": True},
                    )
                    resolved_center = center
            if resolved_center is None and tenant_settings and tenant_settings.default_collection_center_id:
                resolved_center = tenant_settings.default_collection_center
            if resolved_center is None:
                raise serializers.ValidationError(
                    {"registration_center": "Please select a collection center."}
                )
            attrs["registration_center"] = resolved_center
        else:
            # Collection centers OFF: do not require center; if payload has registration_center,
            # accept only if it is a valid CollectionCenter pk; otherwise ignore (set None).
            if reg_center is not None:
                try:
                    CollectionCenter.objects.get(pk=reg_center)
                except (CollectionCenter.DoesNotExist, TypeError):
                    # Invalid or Branch id sent as registration_center — ignore
                    attrs["registration_center"] = None
            # branch field is already popped; no need to set registration_center again

        return attrs

    def create(self, validated_data):
        """Set tenant from request user so patient is visible in tenant-scoped list."""
        request = self.context.get("request")
        if request and getattr(request, "user", None):
            from apps.core.authz import user_tenant

            validated_data["tenant"] = user_tenant(request.user)
        return super().create(validated_data)


class PatientListSerializer(serializers.ModelSerializer):
    """
    A lightweight serializer for listing patients.

    This serializer includes a subset of patient fields for efficient display
    in lists and search results.
    """

    age = serializers.ReadOnlyField()
    full_name = serializers.SerializerMethodField()
    last_order_referred_by = serializers.SerializerMethodField()

    class Meta:
        model = Patient
        fields = [
            "id",
            "patient_id",
            "first_name",
            "last_name",
            "full_name",
            "date_of_birth",
            "age",
            "gender",
            "phone",
            "default_referred_by",
            "last_order_referred_by",
            "registration_number",
            "created_at",
        ]

    def get_full_name(self, obj):
        """
        Return the patient's full name.

        Args:
            obj (Patient): The patient instance.

        Returns:
            str: The concatenated first and last name.
        """
        return obj.get_full_name()

    def get_last_order_referred_by(self, obj):
        """
        Return the referrer of the patient's most recent order.

        If the queryset used to fetch patients has been prefetched with
        'latest_orders' attribute, that value will be used directly to avoid
        issuing an extra database query per patient.

        If no such prefetch is present, this method falls back to querying
        the related 'orders' for the latest one.
        """
        # Fast-path: use prefetched latest_orders if available
        if hasattr(obj, "latest_orders") and obj.latest_orders:
            return obj.latest_orders[0].referred_by

        # Fallback: compute from the related orders (may incur N+1 query)
        last_order = obj.orders.order_by("-created_at").first()
        return last_order.referred_by if last_order else None
