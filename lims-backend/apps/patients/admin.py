"""
Django admin configuration for patients app.
"""

from django.contrib import admin

from .models import Patient


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    """
    Admin configuration for Patient model.
    """

    list_display = [
        "patient_id",
        "first_name",
        "last_name",
        "gender",
        "age",
        "phone",
        "created_at",
    ]
    list_filter = ["gender", "created_at"]
    search_fields = ["patient_id", "first_name", "last_name", "phone", "national_id"]
    readonly_fields = ["patient_id", "created_at", "updated_at", "created_by"]
    ordering = ["-created_at"]

    fieldsets = (
        (
            "Patient Information",
            {
                "fields": (
                    "patient_id",
                    "first_name",
                    "last_name",
                    "date_of_birth",
                    "gender",
                )
            },
        ),
        ("Contact Details", {"fields": ("phone", "email", "address")}),
        ("Identification", {"fields": ("national_id",)}),
        (
            "Metadata",
            {
                "fields": ("created_at", "updated_at", "created_by"),
                "classes": ("collapse",),
            },
        ),
    )
