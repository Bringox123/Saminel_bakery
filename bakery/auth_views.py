from datetime import timedelta
from functools import wraps

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import (
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.core.mail import send_mail
from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views.decorators.http import require_POST

from .forms import (
    AccountSettingsForm,
    AddressForm,
    LoginForm,
    PaymentMethodForm,
    ProfilePictureForm,
    SignUpForm,
)
from .models import SecurityEvent, UserProfile
from .models import Address, Order, PaymentMethod

User = get_user_model()

MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_MINUTES = 15


def _client_ip(request: HttpRequest) -> str:
    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


def _user_agent(request: HttpRequest) -> str:
    return request.META.get('HTTP_USER_AGENT', '')[:255]


def _log_event(user, event_type: str, message: str, request: HttpRequest | None = None) -> None:
    SecurityEvent.objects.create(
        user=user,
        event_type=event_type,
        message=message,
        ip_address=_client_ip(request) if request else None,
        user_agent=_user_agent(request) if request else '',
    )


def _send_verification_email(request: HttpRequest, user) -> None:
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    verify_path = reverse('bakery:verify_email', kwargs={'uidb64': uid, 'token': token})
    verify_url = request.build_absolute_uri(verify_path)

    send_mail(
        subject='Verify your Saminel Flame account',
        message=(
            'Welcome to Saminel Flame.\n\n'
            'Please verify your email address by clicking the link below:\n'
            f'{verify_url}\n\n'
            'If you did not create this account, please ignore this email.'
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=True,
    )


def _send_security_email(user, subject: str, body: str) -> None:
    if not user.email:
        return
    send_mail(
        subject=subject,
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=True,
    )


def _user_role(user) -> str:
    profile, _ = UserProfile.objects.get_or_create(user=user)
    if user.is_superuser or user.is_staff:
        return UserProfile.ROLE_ADMIN
    return profile.role


def role_required(*allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapped(request, *args, **kwargs):
            if _user_role(request.user) not in allowed_roles:
                return redirect('bakery:access_denied')
            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator


def register(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect('bakery:dashboard')

    form = SignUpForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        user = form.save()
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.email_verified = False
        profile.role = UserProfile.ROLE_REGULAR
        profile.save(update_fields=['email_verified', 'role'])

        request.session['pending_verification_user_id'] = user.pk
        _send_verification_email(request, user)

        messages.success(request, 'Account created. Check your email for a verification link.')
        return redirect('bakery:email_verification_pending')

    return render(request, 'bakery/auth/register.html', {'form': form})


def email_verification_pending(request: HttpRequest) -> HttpResponse:
    pending_user_id = request.session.get('pending_verification_user_id')
    pending_user = User.objects.filter(pk=pending_user_id).first() if pending_user_id else None

    return render(
        request,
        'bakery/auth/verify_email_pending.html',
        {'pending_email': pending_user.email if pending_user else ''},
    )


@require_POST
def resend_verification_email(request: HttpRequest) -> HttpResponse:
    pending_user_id = request.session.get('pending_verification_user_id')
    user = User.objects.filter(pk=pending_user_id).first() if pending_user_id else None

    if user and not user.is_active:
        _send_verification_email(request, user)
        messages.success(request, 'Verification email sent again.')
    else:
        messages.error(request, 'No pending account was found for verification.')

    return redirect('bakery:email_verification_pending')


def verify_email(request: HttpRequest, uidb64: str, token: str) -> HttpResponse:
    user = None

    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    is_valid = bool(user and default_token_generator.check_token(user, token))

    if is_valid and user:
        user.is_active = True
        user.save(update_fields=['is_active'])

        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.email_verified = True
        profile.save(update_fields=['email_verified'])

        _log_event(
            user,
            SecurityEvent.EVENT_EMAIL_VERIFIED,
            'Email verification completed successfully.',
            request,
        )
        login(request, user, backend='bakery.auth_backends.EmailOrUsernameBackend')
        messages.success(request, 'Your email is verified. Welcome back!')

    return render(
        request,
        'bakery/auth/verify_email_result.html',
        {'is_valid': is_valid},
    )


def login_view(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect('bakery:dashboard')

    if request.session.pop('session_timed_out', False):
        messages.info(request, 'You were logged out due to inactivity.')

    form = LoginForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        identifier = form.cleaned_data['identifier'].strip()
        password = form.cleaned_data['password']
        remember_me = form.cleaned_data['remember_me']

        candidate = User.objects.filter(
            Q(username__iexact=identifier) | Q(email__iexact=identifier)
        ).first()

        profile = None
        if candidate:
            profile, _ = UserProfile.objects.get_or_create(user=candidate)

            if profile.is_locked:
                lock_end = profile.locked_until or timezone.now()
                remaining = int((lock_end - timezone.now()).total_seconds() // 60) + 1
                form.add_error(None, f'Account locked. Try again in about {remaining} minute(s).')
                return render(request, 'bakery/auth/login.html', {'form': form})

            if not candidate.is_active and not profile.email_verified:
                request.session['pending_verification_user_id'] = candidate.pk
                form.add_error(None, 'Please verify your email before logging in.')
                return render(request, 'bakery/auth/login.html', {'form': form})

        user = authenticate(request, username=identifier, password=password)
        if not user:
            if candidate and profile:
                profile.failed_login_attempts += 1
                update_fields = ['failed_login_attempts']

                _log_event(
                    candidate,
                    SecurityEvent.EVENT_LOGIN_FAILURE,
                    'Failed login attempt recorded.',
                    request,
                )

                if profile.failed_login_attempts >= MAX_LOGIN_ATTEMPTS:
                    profile.locked_until = timezone.now() + timedelta(minutes=LOCKOUT_MINUTES)
                    profile.failed_login_attempts = 0
                    update_fields = ['failed_login_attempts', 'locked_until']
                    _log_event(
                        candidate,
                        SecurityEvent.EVENT_ACCOUNT_LOCKED,
                        'Account locked due to repeated failed login attempts.',
                        request,
                    )
                    _send_security_email(
                        candidate,
                        'Saminel Flame account locked',
                        (
                            'Your account has been temporarily locked after multiple failed login attempts. '
                            f'Please try again in {LOCKOUT_MINUTES} minutes.'
                        ),
                    )

                profile.save(update_fields=update_fields)

            form.add_error(None, 'Invalid email/username or password.')
            return render(request, 'bakery/auth/login.html', {'form': form})

        login(request, user)
        if remember_me:
            request.session.set_expiry(getattr(settings, 'SESSION_COOKIE_AGE', 1209600))
        else:
            request.session.set_expiry(0)

        profile, _ = UserProfile.objects.get_or_create(user=user)
        prior_ip = profile.last_login_ip or ''
        prior_agent = profile.last_user_agent or ''
        current_ip = _client_ip(request)
        current_agent = _user_agent(request)

        profile.failed_login_attempts = 0
        profile.locked_until = None
        profile.last_login_ip = current_ip
        profile.last_user_agent = current_agent
        profile.save(
            update_fields=['failed_login_attempts', 'locked_until', 'last_login_ip', 'last_user_agent']
        )

        if prior_ip and (prior_ip != current_ip or prior_agent != current_agent):
            _log_event(
                user,
                SecurityEvent.EVENT_NEW_DEVICE_LOGIN,
                'Login detected from a different device or location.',
                request,
            )
            _send_security_email(
                user,
                'New login detected on your Saminel Flame account',
                (
                    'We noticed a login from a new device or browser.\n'
                    f'IP: {current_ip or "Unknown"}\n'
                    'If this was not you, reset your password immediately.'
                ),
            )

        next_url = request.POST.get('next') or request.GET.get('next')
        return redirect(next_url or 'bakery:dashboard')

    return render(request, 'bakery/auth/login.html', {'form': form})


@require_POST
def logout_view(request: HttpRequest) -> HttpResponse:
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('bakery:home')


@login_required
def dashboard(request: HttpRequest) -> HttpResponse:
    current_user = User.objects.get(pk=request.user.pk)
    profile, _ = UserProfile.objects.get_or_create(user=current_user)
    return render(
        request,
        'bakery/auth/dashboard.html',
        {
            'profile': profile,
            'orders': Order.objects.filter(user=current_user).select_related('shipping_address')[:20],
            'addresses': Address.objects.filter(user=current_user)[:10],
            'payment_methods': PaymentMethod.objects.filter(user=current_user)[:10],
            'security_events': SecurityEvent.objects.filter(user=current_user)[:10],
        },
    )


@login_required
def profile_settings(request: HttpRequest) -> HttpResponse:
    current_user = User.objects.get(pk=request.user.pk)
    profile, _ = UserProfile.objects.get_or_create(user=current_user)

    account_form = AccountSettingsForm(instance=current_user)
    picture_form = ProfilePictureForm(instance=profile)
    address_form = AddressForm()
    payment_form = PaymentMethodForm()

    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        if form_type == 'account':
            account_form = AccountSettingsForm(request.POST, instance=current_user)
            picture_form = ProfilePictureForm(request.POST, request.FILES, instance=profile)
            if account_form.is_valid() and picture_form.is_valid():
                account_form.save()
                picture_form.save()
                messages.success(request, 'Account profile updated successfully.')
                return redirect('bakery:profile_settings')

        elif form_type == 'address':
            address_form = AddressForm(request.POST)
            if address_form.is_valid():
                address = address_form.save(commit=False)
                address.user = current_user
                address.save()
                messages.success(request, 'Address saved successfully.')
                return redirect('bakery:profile_settings')

        elif form_type == 'payment':
            payment_form = PaymentMethodForm(request.POST)
            if payment_form.is_valid():
                payment_method = payment_form.save(commit=False)
                payment_method.user = current_user
                payment_method.save()
                messages.success(request, 'Payment method saved successfully.')
                return redirect('bakery:profile_settings')

    return render(
        request,
        'bakery/auth/profile_settings.html',
        {
            'profile': profile,
            'account_form': account_form,
            'picture_form': picture_form,
            'address_form': address_form,
            'payment_form': payment_form,
            'addresses': Address.objects.filter(user=current_user)[:20],
            'payment_methods': PaymentMethod.objects.filter(user=current_user)[:20],
        },
    )


@role_required(UserProfile.ROLE_MODERATOR, UserProfile.ROLE_ADMIN)
def moderator_console(request: HttpRequest) -> HttpResponse:
    return render(
        request,
        'bakery/auth/moderator_console.html',
        {'events': SecurityEvent.objects.select_related('user').all()[:50]},
    )


@login_required
def access_denied(request: HttpRequest) -> HttpResponse:
    return render(request, 'bakery/auth/access_denied.html', status=403)


class AppPasswordResetView(PasswordResetView):
    template_name = 'registration/password_reset_form.html'
    email_template_name = 'registration/password_reset_email.txt'
    subject_template_name = 'registration/password_reset_subject.txt'
    success_url = reverse_lazy('bakery:password_reset_done')


class AppPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'registration/password_reset_done.html'


class AppPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'registration/password_reset_confirm.html'
    success_url = reverse_lazy('bakery:password_reset_complete')


class AppPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'registration/password_reset_complete.html'


@login_required
def change_password(request: HttpRequest) -> HttpResponse:
    current_user = User.objects.get(pk=request.user.pk)
    form = PasswordChangeForm(user=current_user, data=request.POST or None)

    if request.method == 'POST' and form.is_valid():
        form.save()
        _log_event(
            request.user,
            SecurityEvent.EVENT_PASSWORD_CHANGED,
            'Password changed successfully.',
            request,
        )
        _send_security_email(
            request.user,
            'Your Saminel Flame password was changed',
            'Your account password was changed successfully. If this was not you, reset it immediately.',
        )
        messages.success(request, 'Password updated successfully. Please log in again.')
        logout(request)
        return redirect('bakery:login')

    return render(request, 'bakery/auth/change_password.html', {'form': form})
