"""Management command to seed demo data."""

from datetime import date

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from catalog.models import TestCatalog
from patients.models import Patient

User = get_user_model()


class Command(BaseCommand):
    """Seed demo data for LIMS."""

    help = "Seed demo data for LIMS"

    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            "--no-input",
            action="store_true",
            help="Run without user interaction (idempotent)",
        )

    def handle(self, *args, **kwargs):
        """Handle the command."""
        self.stdout.write("Seeding demo data...")

        # Create users
        admin, _ = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@alshifa.com",
                "role": "ADMIN",
                "first_name": "Admin",
                "last_name": "User",
            },
        )
        admin.set_password("admin123")
        admin.save()

        reception, _ = User.objects.get_or_create(
            username="reception",
            defaults={
                "email": "reception@alshifa.com",
                "role": "RECEPTION",
                "first_name": "Reception",
                "last_name": "User",
            },
        )
        reception.set_password("reception123")
        reception.save()

        # Phlebotomy user (also used for sample collection)
        phlebotomy, _ = User.objects.get_or_create(
            username="phlebotomy",
            defaults={
                "email": "phlebotomy@alshifa.com",
                "role": "PHLEBOTOMY",
                "first_name": "Phlebotomy",
                "last_name": "User",
            },
        )
        phlebotomy.set_password("phlebotomy123")
        phlebotomy.save()

        tech, _ = User.objects.get_or_create(
            username="tech",
            defaults={
                "email": "tech@alshifa.com",
                "role": "TECHNOLOGIST",
                "first_name": "Tech",
                "last_name": "User",
            },
        )
        tech.set_password("tech123")
        tech.save()

        pathologist, _ = User.objects.get_or_create(
            username="pathologist",
            defaults={
                "email": "path@alshifa.com",
                "role": "PATHOLOGIST",
                "first_name": "Dr. Muhammad Munaim",
                "last_name": "Tahir",
            },
        )
        pathologist.set_password("path123")
        pathologist.save()

        # Multi-role user for reception, phlebotomy, and result entry
        # This user has RECEPTION role but can perform multiple tasks
        # through permissions
        multi_role, _ = User.objects.get_or_create(
            username="staff",
            defaults={
                "email": "staff@alshifa.com",
                "role": "RECEPTION",  # Primary role
                "first_name": "Staff",
                "last_name": "User",
            },
        )
        multi_role.set_password("staff123")
        multi_role.save()

        # Verification user (pathologist role)
        verifier, _ = User.objects.get_or_create(
            username="verifier",
            defaults={
                "email": "verifier@alshifa.com",
                "role": "PATHOLOGIST",
                "first_name": "Verification",
                "last_name": "User",
            },
        )
        verifier.set_password("verify123")
        verifier.save()

        self.stdout.write(self.style.SUCCESS("✓ Created users"))

        # Create test catalog
        tests_data = [
            {
                "code": "CBC",
                "name": "Complete Blood Count",
                "category": "Hematology",
                "sample_type": "Blood",
                "price": 500.00,
                "turnaround_time_hours": 24,
                "description": "Complete blood count with differential",
            },
            {
                "code": "LFT",
                "name": "Liver Function Test",
                "category": "Biochemistry",
                "sample_type": "Blood",
                "price": 800.00,
                "turnaround_time_hours": 48,
                "description": "Comprehensive liver panel",
            },
            {
                "code": "RFT",
                "name": "Renal Function Test",
                "category": "Biochemistry",
                "sample_type": "Blood",
                "price": 700.00,
                "turnaround_time_hours": 48,
                "description": "Kidney function markers",
            },
            {
                "code": "LIPID",
                "name": "Lipid Profile",
                "category": "Biochemistry",
                "sample_type": "Blood",
                "price": 600.00,
                "turnaround_time_hours": 24,
                "description": "Cholesterol and triglycerides panel",
            },
            {
                "code": "HBA1C",
                "name": "Glycated Hemoglobin",
                "category": "Biochemistry",
                "sample_type": "Blood",
                "price": 900.00,
                "turnaround_time_hours": 72,
                "description": "Diabetes monitoring test",
            },
        ]

        for test_data in tests_data:
            TestCatalog.objects.get_or_create(
                code=test_data["code"], defaults=test_data
            )

        self.stdout.write(
            self.style.SUCCESS(f"✓ Created {len(tests_data)} test catalog items")
        )

        # Create sample patients
        patients_data = [
            {
                "full_name": "Muhammad Ahmed",
                "father_name": "Abdul Rahman",
                "dob": date(1985, 5, 15),
                "sex": "M",
                "phone": "03001234567",
                "cnic": "12345-1234567-1",
                "address": "House 123, Street 4, Islamabad",
            },
            {
                "full_name": "Fatima Zahra",
                "father_name": "Muhammad Ali",
                "dob": date(1990, 8, 20),
                "sex": "F",
                "phone": "03009876543",
                "cnic": "12345-1234567-2",
                "address": "Flat 45, Block B, Lahore",
            },
        ]

        for patient_data in patients_data:
            Patient.objects.get_or_create(
                cnic=patient_data["cnic"], defaults=patient_data
            )

        self.stdout.write(
            self.style.SUCCESS(f"✓ Created {len(patients_data)} sample patients")
        )
        self.stdout.write(self.style.SUCCESS("\nDemo data seeded successfully! 🎉"))
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("DEMO LOGIN CREDENTIALS:")
        self.stdout.write("=" * 60)
        self.stdout.write("\n🔑 Administrator:")
        self.stdout.write("   Username: admin")
        self.stdout.write("   Password: admin123")
        self.stdout.write("   Role: ADMIN (Full system access)")
        self.stdout.write("\n👥 Multi-Role Staff (Reception/Phlebotomy/Entry):")
        self.stdout.write("   Username: staff")
        self.stdout.write("   Password: staff123")
        self.stdout.write(
            "   Role: RECEPTION (Can perform registration, collection, entry)"
        )
        self.stdout.write("\n✅ Verification User:")
        self.stdout.write("   Username: verifier")
        self.stdout.write("   Password: verify123")
        self.stdout.write("   Role: PATHOLOGIST (Result verification & publishing)")
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("Additional Individual Role Users:")
        self.stdout.write("=" * 60)
        self.stdout.write("   reception / reception123 (Reception only)")
        self.stdout.write("   phlebotomy / phlebotomy123 (Phlebotomy only)")
        self.stdout.write("   tech / tech123 (Technologist only)")
        self.stdout.write("   pathologist / path123 (Pathologist only)")
        self.stdout.write("=" * 60 + "\n")
