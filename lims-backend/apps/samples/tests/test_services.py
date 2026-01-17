"""
Tests for sample generation service.
"""

from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.patients.models import Patient
from apps.laboratory.models import Test, TestCategory
from apps.orders.models import Order, OrderItem
from apps.billing.models import Payment
from apps.samples.models import Sample, SampleStatus
from apps.samples.services import generate_samples_for_order, ensure_samples_for_paid_order

User = get_user_model()


class SampleGenerationTestCase(TestCase):
    """Test cases for automatic sample generation on payment."""
    
    def setUp(self):
        """Set up test data."""
        # Create user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@test.com',
            full_name='Test User'
        )
        
        # Create patient
        self.patient = Patient.objects.create(
            first_name='John',
            last_name='Doe',
            date_of_birth='1990-01-01',
            gender='Male',
            phone='1234567890',
            created_by=self.user
        )
        
        # Create test category and tests
        self.category = TestCategory.objects.create(
            category_name='Hematology',
            category_code='HEM'
        )
        
        self.test_cbc = Test.objects.create(
            test_code='CBC',
            test_name='Complete Blood Count',
            category=self.category,
            price=Decimal('50.00')
        )
        
        self.test_ua = Test.objects.create(
            test_code='UA',
            test_name='Urinalysis',
            category=self.category,
            price=Decimal('30.00')
        )
        
        # Create order with items
        self.order = Order.objects.create(
            patient=self.patient,
            ordered_by=self.user,
            total_amount=Decimal('80.00'),
            net_amount=Decimal('80.00'),
            is_paid=False
        )
        
        self.order_item_1 = OrderItem.objects.create(
            order=self.order,
            test=self.test_cbc,
            price=Decimal('50.00')
        )
        
        self.order_item_2 = OrderItem.objects.create(
            order=self.order,
            test=self.test_ua,
            price=Decimal('30.00')
        )
    
    def test_no_samples_generated_for_unpaid_order(self):
        """Samples should not be generated for unpaid orders."""
        self.order.is_paid = False
        self.order.save()
        
        samples = generate_samples_for_order(self.order, self.user)
        
        self.assertEqual(len(samples), 0)
        self.assertEqual(Sample.objects.filter(order_item__order=self.order).count(), 0)
    
    def test_samples_generated_when_payment_recorded(self):
        """Samples should be auto-generated when order is fully paid."""
        # Initially no samples
        self.assertEqual(Sample.objects.count(), 0)
        
        # Record full payment
        payment = Payment.objects.create(
            order=self.order,
            amount=Decimal('80.00'),
            payment_method='cash',
            recorded_by=self.user
        )
        
        # Check order is marked as paid
        self.order.refresh_from_db()
        self.assertTrue(self.order.is_paid)
        
        # Check samples were created
        samples = Sample.objects.filter(order_item__order=self.order)
        self.assertEqual(samples.count(), 2)
        
        # Check sample details
        sample_1 = samples.filter(order_item=self.order_item_1).first()
        self.assertIsNotNone(sample_1)
        self.assertEqual(sample_1.status, SampleStatus.PENDING)
        self.assertEqual(sample_1.sample_type, 'Blood')
        self.assertIsNotNone(sample_1.barcode)
        self.assertTrue(sample_1.barcode.startswith('SAM-'))
        
        sample_2 = samples.filter(order_item=self.order_item_2).first()
        self.assertIsNotNone(sample_2)
        self.assertEqual(sample_2.sample_type, 'Urine')  # Should detect from test name
    
    def test_idempotency_no_duplicate_samples(self):
        """Sample generation should be idempotent - no duplicates."""
        # Mark order as paid and generate samples
        self.order.is_paid = True
        self.order.save()
        
        # First generation
        samples_1 = generate_samples_for_order(self.order, self.user)
        self.assertEqual(len(samples_1), 2)
        
        # Second generation attempt
        samples_2 = generate_samples_for_order(self.order, self.user)
        self.assertEqual(len(samples_2), 0)  # No new samples created
        
        # Total samples should still be 2
        total_samples = Sample.objects.filter(order_item__order=self.order).count()
        self.assertEqual(total_samples, 2)
    
    def test_partial_payment_no_samples(self):
        """Samples should not be generated for partial payment."""
        # Record partial payment (50 out of 80)
        payment = Payment.objects.create(
            order=self.order,
            amount=Decimal('50.00'),
            payment_method='cash',
            recorded_by=self.user
        )
        
        self.order.refresh_from_db()
        self.assertFalse(self.order.is_paid)
        
        # No samples should exist
        self.assertEqual(Sample.objects.count(), 0)
    
    def test_multiple_payments_trigger_sample_generation_once(self):
        """Multiple payments reaching full amount should generate samples only once."""
        # First partial payment
        payment_1 = Payment.objects.create(
            order=self.order,
            amount=Decimal('50.00'),
            payment_method='cash',
            recorded_by=self.user
        )
        
        self.order.refresh_from_db()
        self.assertFalse(self.order.is_paid)
        self.assertEqual(Sample.objects.count(), 0)
        
        # Second payment completing the order
        payment_2 = Payment.objects.create(
            order=self.order,
            amount=Decimal('30.00'),
            payment_method='cash',
            recorded_by=self.user
        )
        
        self.order.refresh_from_db()
        self.assertTrue(self.order.is_paid)
        
        # Samples should be created
        self.assertEqual(Sample.objects.count(), 2)
        
        # Third payment (overpayment) should not create more samples
        payment_3 = Payment.objects.create(
            order=self.order,
            amount=Decimal('10.00'),
            payment_method='cash',
            recorded_by=self.user
        )
        
        # Still only 2 samples
        self.assertEqual(Sample.objects.count(), 2)
    
    def test_sample_barcode_uniqueness(self):
        """Each generated sample should have a unique barcode."""
        self.order.is_paid = True
        self.order.save()
        
        samples = generate_samples_for_order(self.order, self.user)
        
        barcodes = [s.barcode for s in samples]
        self.assertEqual(len(barcodes), len(set(barcodes)))  # All unique
    
    def test_ensure_samples_wrapper_function(self):
        """Test the ensure_samples_for_paid_order wrapper function."""
        self.order.is_paid = True
        self.order.save()
        
        samples = ensure_samples_for_paid_order(self.order, self.user)
        
        self.assertEqual(len(samples), 2)
        self.assertEqual(Sample.objects.count(), 2)
