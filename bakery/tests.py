from django.test import TestCase
from django.urls import reverse
from .models import Category, Product


class BakeryViewsTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name='Bread')
        Product.objects.create(
            name='Sourdough Loaf',
            description='Naturally leavened loaf with a crisp crust.',
            price='7.50',
            category=category,
            is_featured=True,
        )

    def test_home_page_renders(self):
        response = self.client.get(reverse('bakery:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sourdough Loaf')

    def test_product_detail_page_renders(self):
        product = Product.objects.first()
        response = self.client.get(reverse('bakery:product_detail', args=[product.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, product.name)

    def test_pos_terminal_renders(self):
        response = self.client.get(reverse('bakery:pos_terminal'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Offline-First Point of Sale')

    def test_cart_page_renders(self):
        response = self.client.get(reverse('bakery:cart'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Your Bakery Cart')

    def test_offline_order_sync_endpoint(self):
        import json
        payload = {
            'orders': [
                {
                    'clientOrderId': 'LOCAL-TEST-001',
                    'totalAmount': '15.00',
                    'notes': 'Counter pickup',
                    'items': [{'name': 'Sourdough Loaf', 'quantity': 2, 'price': 7.5}],
                }
            ]
        }
        response = self.client.post(
            reverse('bakery:sync_offline_orders'),
            data=json.dumps(payload),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'ok')
        self.assertIn('LOCAL-TEST-001', data['synced_client_ids'])

    def test_user_registration(self):
        response = self.client.post(
            reverse('bakery:register'),
            data={
                'email': 'customer@example.com',
                'username': 'customer1',
                'password1': 'Saminel@2026!',
                'password2': 'Saminel@2026!',
                'accept_terms': 'on',
            },
        )
        self.assertEqual(response.status_code, 302)
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.assertTrue(User.objects.filter(email='customer@example.com').exists())
