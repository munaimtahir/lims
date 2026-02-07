"""
Django management command to create demo users for all roles.

This command creates demo users for testing and QA purposes.
It is idempotent - safe to run multiple times.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import User


class Command(BaseCommand):
    help = "Create demo users for all roles (idempotent)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing demo users before creating",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["clear"]:
            self.stdout.write(self.style.WARNING("Clearing existing demo users..."))
            User.objects.filter(
                username__in=[
                    "admin",
                    "receptionist",
                    "cashier",
                    "phlebotomist",
                    "labtech",
                    "pathologist",
                    "manager",
                ]
            ).delete()

        self.stdout.write(self.style.SUCCESS("Creating demo users..."))

        demo_users = [
            {
                "username": "admin",
                "email": "admin@lims.demo",
                "full_name": "Admin User",
                "role": "Admin",
                "password": "admin123",
                "is_staff": True,
                "is_superuser": True,
            },
            {
                "username": "receptionist",
                "email": "receptionist@lims.demo",
                "full_name": "Receptionist User",
                "role": "Receptionist",
                "password": "recep123",
            },
            {
                "username": "cashier",
                "email": "cashier@lims.demo",
                "full_name": "Cashier User",
                "role": "Cashier",
                "password": "cash123",
            },
            {
                "username": "phlebotomist",
                "email": "phlebotomist@lims.demo",
                "full_name": "Phlebotomist User",
                "role": "Phlebotomist",
                "password": "phleb123",
            },
            {
                "username": "labtech",
                "email": "labtech@lims.demo",
                "full_name": "Lab Technician User",
                "role": "Lab Technician",
                "password": "labtech123",
            },
            {
                "username": "pathologist",
                "email": "pathologist@lims.demo",
                "full_name": "Dr. Pathologist",
                "role": "Pathologist",
                "password": "patho123",
            },
            {
                "username": "manager",
                "email": "manager@lims.demo",
                "full_name": "Manager User",
                "role": "Manager",
                "password": "manager123",
            },
        ]

        created_users = []
        for user_data in demo_users:
            password = user_data.pop("password")
            username = user_data["username"]

            user, created = User.objects.get_or_create(
                username=username, defaults=user_data
            )

            # Always update password to ensure it's set correctly
            user.set_password(password)
            user.save()

            if created:
                self.stdout.write(f"  Created user: {username} ({user_data['role']})")
            else:
                self.stdout.write(f"  Updated user: {username} ({user_data['role']})")

            created_users.append(
                {
                    "username": username,
                    "password": password,
                    "role": user_data["role"],
                }
            )

        self.stdout.write(self.style.SUCCESS("\n" + "=" * 60))
        self.stdout.write(self.style.SUCCESS("DEMO USERS SUMMARY"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write("\n")
        self.stdout.write(f"{'Username':<15} {'Role':<20} {'Password':<15}")
        self.stdout.write("-" * 60)
        for user in created_users:
            self.stdout.write(
                f"{user['username']:<15} {user['role']:<20} {user['password']:<15}"
            )
        self.stdout.write("\n")
        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully created/updated {len(created_users)} demo users"
            )
        )
