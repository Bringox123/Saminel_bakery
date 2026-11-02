import json
from decimal import Decimal, InvalidOperation

from django.contrib.auth import get_user_model
from django.http import HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from .models import Category, Order, Product

User = get_user_model()


def home(request: HttpRequest):
    featured_products = Product.objects.filter(is_featured=True).select_related('category')[:6]
    return render(
        request,
        'bakery/home.html',
        {'featured_products': featured_products},
    )


def product_detail(request: HttpRequest, pk: int):
    product = get_object_or_404(Product.objects.select_related('category'), pk=pk)
    return render(request, 'bakery/product_detail.html', {'product': product})


def product_list(request: HttpRequest):
    products = Product.objects.select_related('category').order_by('category__name', 'name')
    return render(request, 'bakery/product_list.html', {'products': products})


def cart(request: HttpRequest):
    products = Product.objects.select_related('category').order_by('name')
    return render(request, 'bakery/cart.html', {'products': products})


def pos_terminal(request: HttpRequest):
    categories = Category.objects.order_by('name')
    products = Product.objects.select_related('category').order_by('category__name', 'name')
    return render(
        request,
        'bakery/pos.html',
        {
            'categories': categories,
            'products': products,
        },
    )


@require_POST
def sync_offline_orders(request: HttpRequest):
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON payload.'}, status=400)

    orders_data = payload.get('orders', [])
    if not isinstance(orders_data, list):
        return JsonResponse({'error': 'Orders field must be a list.'}, status=400)

    target_user = request.user if request.user.is_authenticated else User.objects.order_by('pk').first()
    synced_client_ids: list[str] = []
    created_orders: list[dict] = []

    for entry in orders_data[:50]:
        if not isinstance(entry, dict):
            continue
        client_id = str(entry.get('clientOrderId', '')).strip()[:64]
        raw_total = entry.get('totalAmount', '0')
        notes = str(entry.get('notes', '')).strip()[:500]
        items = entry.get('items', [])

        try:
            total_amount = max(Decimal(str(raw_total)), Decimal('0.00'))
        except (InvalidOperation, ValueError):
            total_amount = Decimal('0.00')

        item_summary = ', '.join(
            f"{int(i.get('quantity', 1))}x {str(i.get('name', 'Item'))[:60]}"
            for i in items
            if isinstance(i, dict)
        )[:350]
        combined_notes = f"[POS/Sync {client_id}] {item_summary}".strip()
        if notes:
            combined_notes = f"{combined_notes} | Note: {notes}"

        if target_user is not None:
            order = Order.objects.create(
                user=target_user,
                total_amount=total_amount,
                notes=combined_notes,
                status=Order.STATUS_PENDING,
            )
            created_orders.append(
                {
                    'order_number': order.order_number,
                    'client_order_id': client_id,
                    'total_amount': str(order.total_amount),
                }
            )
        if client_id:
            synced_client_ids.append(client_id)

    return JsonResponse(
        {
            'status': 'ok',
            'synced_client_ids': synced_client_ids,
            'orders': created_orders,
        }
    )
