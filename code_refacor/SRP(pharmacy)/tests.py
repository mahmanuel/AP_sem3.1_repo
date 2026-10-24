from datetime import date
from decimal import Decimal

from django.test import TestCase

from pharmacy.models import Category, MedicineItem, Purchase, PurchaseItem, Supplier
from pharmacy.services import create_purchase_order
from users.models import User


class CreatePurchaseOrderTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='pharmacist',
            password='test-password',
            role=User.PHARMACIST,
        )
        self.supplier = Supplier.objects.create(
            name='Example Supplier',
            phone='555-0100',
            address='1 Example Street',
        )
        self.category = Category.objects.create(name='Medicine')
        self.medicine = MedicineItem.objects.create(
            name='Example Medicine',
            category=self.category,
            supplier=self.supplier,
            purchase_price=Decimal('2.00'),
            selling_price=Decimal('3.00'),
        )

    def test_creates_purchase_items_and_total(self):
        purchase = create_purchase_order(
            supplier_id=self.supplier.pk,
            purchase_date=date(2026, 10, 24),
            notes='Urgent restock',
            created_by=self.user,
            items=[{
                'medicine_id': self.medicine.pk,
                'quantity': 3,
                'unit_price': Decimal('4.50'),
                'batch_number': 'BATCH-1',
                'expiry_date': date(2027, 10, 24),
            }],
        )

        item = PurchaseItem.objects.get(purchase=purchase)
        self.assertEqual(purchase.status, Purchase.PENDING)
        self.assertEqual(purchase.payment_status, 'Unpaid')
        self.assertEqual(purchase.total_amount, Decimal('13.50'))
        self.assertEqual(item.medicine, self.medicine)
        self.assertEqual(item.batch_number, 'BATCH-1')
        self.assertEqual(item.expiry_date, date(2027, 10, 24))

    def test_rolls_back_order_if_an_item_cannot_be_created(self):
        with self.assertRaises(MedicineItem.DoesNotExist):
            create_purchase_order(
                supplier_id=self.supplier.pk,
                purchase_date=date(2026, 10, 24),
                notes='',
                created_by=self.user,
                items=[{
                    'medicine_id': 999999,
                    'quantity': 3,
                    'unit_price': Decimal('4.50'),
                    'batch_number': None,
                    'expiry_date': None,
                }],
            )

        self.assertEqual(Purchase.objects.count(), 0)
