from django.contrib import admin
from .models import (
    Address,
    Category,
    Order,
    PaymentMethod,
    Product,
    SecurityEvent,
    UserProfile,
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'is_featured', 'has_image')
    list_filter = ('category', 'is_featured')
    search_fields = ('name', 'description')
    fields = ('name', 'description', 'price', 'category', 'is_featured', 'image')

    @admin.display(boolean=True, description='Image')
    def has_image(self, obj):
        return bool(obj.image)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'email_verified', 'is_locked', 'failed_login_attempts')
    list_filter = ('role', 'email_verified')
    search_fields = ('user__username', 'user__email')


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'label', 'city', 'country', 'is_default')
    list_filter = ('country', 'is_default')
    search_fields = ('user__username', 'full_name', 'line1', 'city')


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('user', 'method_type', 'provider', 'last4', 'is_default')
    list_filter = ('method_type', 'is_default')
    search_fields = ('user__username', 'provider', 'account_name', 'token_reference')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'status', 'total_amount', 'placed_at')
    list_filter = ('status', 'placed_at')
    search_fields = ('order_number', 'user__username', 'user__email')


@admin.register(SecurityEvent)
class SecurityEventAdmin(admin.ModelAdmin):
    list_display = ('user', 'event_type', 'message', 'ip_address', 'created_at')
    list_filter = ('event_type', 'created_at')
    search_fields = ('user__username', 'user__email', 'message', 'ip_address')
