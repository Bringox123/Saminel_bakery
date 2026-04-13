import uuid

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self) -> str:
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=150)
    description = models.TextField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    is_featured = models.BooleanField(default=False)
    image = models.ImageField(upload_to='products/', blank=True, null=True)

    def __str__(self) -> str:
        return self.name


def generate_order_number() -> str:
    return f"SF-{uuid.uuid4().hex[:10].upper()}"


class UserProfile(models.Model):
    ROLE_REGULAR = 'regular'
    ROLE_MODERATOR = 'moderator'
    ROLE_ADMIN = 'admin'
    ROLE_CHOICES = [
        (ROLE_REGULAR, 'Regular User'),
        (ROLE_MODERATOR, 'Moderator'),
        (ROLE_ADMIN, 'Admin'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=12, choices=ROLE_CHOICES, default=ROLE_REGULAR)
    email_verified = models.BooleanField(default=False)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    failed_login_attempts = models.PositiveIntegerField(default=0)
    locked_until = models.DateTimeField(blank=True, null=True)
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)
    last_user_agent = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Profile for {self.user.username}"

    @property
    def is_locked(self) -> bool:
        return bool(self.locked_until and self.locked_until > timezone.now())


class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='addresses')
    label = models.CharField(max_length=30, default='Home')
    full_name = models.CharField(max_length=120)
    line1 = models.CharField(max_length=180)
    line2 = models.CharField(max_length=180, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=30)
    country = models.CharField(max_length=80, default='Ghana')
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_default', '-created_at']

    def __str__(self) -> str:
        return f"{self.label} - {self.user.username}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_default:
            Address.objects.filter(user=self.user).exclude(pk=self.pk).update(is_default=False)
        elif not Address.objects.filter(user=self.user, is_default=True).exists():
            self.is_default = True
            super().save(update_fields=['is_default'])


class PaymentMethod(models.Model):
    TYPE_CARD = 'card'
    TYPE_MOBILE_MONEY = 'mobile_money'
    TYPE_BANK_TRANSFER = 'bank_transfer'
    TYPE_CASH_ON_DELIVERY = 'cash_on_delivery'
    METHOD_CHOICES = [
        (TYPE_CARD, 'Card'),
        (TYPE_MOBILE_MONEY, 'Mobile Money'),
        (TYPE_BANK_TRANSFER, 'Bank Transfer'),
        (TYPE_CASH_ON_DELIVERY, 'Cash on Delivery'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payment_methods')
    method_type = models.CharField(max_length=20, choices=METHOD_CHOICES)
    provider = models.CharField(max_length=60, blank=True)
    account_name = models.CharField(max_length=120, blank=True)
    last4 = models.CharField(max_length=4, blank=True)
    expiry_month = models.PositiveSmallIntegerField(blank=True, null=True)
    expiry_year = models.PositiveSmallIntegerField(blank=True, null=True)
    token_reference = models.CharField(max_length=120, blank=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_default', '-created_at']

    def __str__(self) -> str:
        suffix = f" ****{self.last4}" if self.last4 else ''
        provider = self.provider or self.get_method_type_display()
        return f"{provider}{suffix}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_default:
            PaymentMethod.objects.filter(user=self.user).exclude(pk=self.pk).update(is_default=False)
        elif not PaymentMethod.objects.filter(user=self.user, is_default=True).exists():
            self.is_default = True
            super().save(update_fields=['is_default'])


class Order(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_PROCESSING = 'processing'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_PROCESSING, 'Processing'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    order_number = models.CharField(max_length=16, unique=True, default=generate_order_number, editable=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    placed_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    shipping_address = models.ForeignKey(
        Address,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='orders',
    )

    class Meta:
        ordering = ['-placed_at']

    def __str__(self) -> str:
        return self.order_number


class SecurityEvent(models.Model):
    EVENT_NEW_DEVICE_LOGIN = 'new_device_login'
    EVENT_PASSWORD_CHANGED = 'password_changed'
    EVENT_ACCOUNT_LOCKED = 'account_locked'
    EVENT_EMAIL_VERIFIED = 'email_verified'
    EVENT_LOGIN_FAILURE = 'login_failure'
    EVENT_CHOICES = [
        (EVENT_NEW_DEVICE_LOGIN, 'New Device Login'),
        (EVENT_PASSWORD_CHANGED, 'Password Changed'),
        (EVENT_ACCOUNT_LOCKED, 'Account Locked'),
        (EVENT_EMAIL_VERIFIED, 'Email Verified'),
        (EVENT_LOGIN_FAILURE, 'Login Failure'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='security_events')
    event_type = models.CharField(max_length=32, choices=EVENT_CHOICES)
    message = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"{self.user.username} - {self.get_event_type_display()}"


User = get_user_model()


@receiver(post_save, sender=User)
def ensure_profile_exists(sender, instance, created, **kwargs):
    profile, _ = UserProfile.objects.get_or_create(user=instance)
    updates: list[str] = []

    if created and instance.is_active and not profile.email_verified:
        profile.email_verified = True
        updates.append('email_verified')

    if (instance.is_staff or instance.is_superuser) and profile.role != UserProfile.ROLE_ADMIN:
        profile.role = UserProfile.ROLE_ADMIN
        updates.append('role')

    if updates:
        profile.save(update_fields=updates)
