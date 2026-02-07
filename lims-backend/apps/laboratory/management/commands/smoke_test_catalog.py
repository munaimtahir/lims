from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.laboratory.models import Test
from apps.orders.models import Order, OrderItem
from apps.patients.models import Patient
from apps.results.models import TestResult

User = get_user_model()


class Command(BaseCommand):
    help = "Run smoke test for catalog usability"

    def handle(self, *args, **options):
        self.stdout.write("Running smoke test...")

        # 1. User
        user = User.objects.first()
        if not user:
            user = User.objects.create_superuser(
                "admin_smoke", "admin@example.com", "admin"
            )
            self.stdout.write("Created superuser admin_smoke")

        # 2. Patient
        patient, _ = Patient.objects.get_or_create(
            mrn="SMOKE001",
            defaults={
                "first_name": "Smoke",
                "last_name": "Test",
                "gender": "Male",
                "age_years": 30,
            },
        )
        self.stdout.write(f"Using Patient: {patient}")

        # 3. Pick Test
        # Pick one that has mappings (either imported or fixed)
        test = Test.objects.filter(test_parameters__isnull=False).first()
        if not test:
            self.stdout.write(self.style.ERROR("FAIL: No usable tests found!"))
            return

        self.stdout.write(f"Selected Test: {test.test_name} ({test.test_code})")

        # 4. Create Order
        order = Order.objects.create(
            patient=patient,
            ordered_by=user,
            total_amount=test.price,
            net_amount=test.price,
            status="NEW",
        )

        # 5. Order Item
        item = OrderItem.objects.create(order=order, test=test, price=test.price)
        self.stdout.write(f"Created Order {order.order_id} Item {item.id}")

        # 6. Enter Results
        # Iterate expected parameters
        params = test.test_parameters.all()
        if not params.exists():
            self.stdout.write(
                self.style.ERROR(
                    "FAIL: Test has no parameters even though filter said yes?"
                )
            )
            return

        for tp in params:
            TestResult.objects.create(
                order_item=item,
                test_parameter=tp,
                result_value="10.5",
                entered_by=user,
                entered_at=timezone.now(),
                status="ENTERED",
            )
            self.stdout.write(
                f"  Entered result for {tp.effective_parameter_name}: 10.5"
            )

        self.stdout.write(self.style.SUCCESS("SMOKE TEST PASS"))
