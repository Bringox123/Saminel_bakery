from django.shortcuts import get_object_or_404, redirect, render
from .models import Product


def home(request):
    featured_products = Product.objects.filter(is_featured=True).select_related('category')[:6]
    return render(
        request,
        'bakery/home.html',
        {'featured_products': featured_products},
    )


def product_detail(request, pk: int):
    product = get_object_or_404(Product.objects.select_related('category'), pk=pk)
    return render(request, 'bakery/product_detail.html', {'product': product})


def product_list(request):
    products = Product.objects.select_related('category').order_by('category__name', 'name')
    return render(request, 'bakery/product_list.html', {'products': products})


def cart(request):
    return redirect('bakery:product_list')
