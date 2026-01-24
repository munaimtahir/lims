from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Seeds users for smoke testing'

    def handle(self, *args, **options):
        users = [
            ("receptionist", "Receptionist", "recep123", "receptionist@example.com", False),
            ("phlebotomist", "Phlebotomist", "phleb123", "phleb@example.com", False),
            ("labtech", "Lab Technician", "labtech123", "labtech@example.com", False),
            ("pathologist", "Pathologist", "patho123", "pathologist@example.com", False),
            ("admin", "Admin", "admin123", "admin@example.com", True),
            ("cashier", "Cashier", "cash123", "cashier@example.com", False),
        ]

        for username, role, password, email, is_admin in users:
            if not User.objects.filter(username=username).exists():
                u = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    role=role,
                    full_name=f"Smoke {role}"
                )
                if is_admin:
                    u.is_staff = True
                    u.is_superuser = True
                    u.save()
                self.stdout.write(self.style.SUCCESS(f"Created user {username}"))
            else:
                self.stdout.write(f"User {username} already exists")
