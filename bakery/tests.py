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
