from django.urls import path
from . import auth_views, views

app_name = 'bakery'

urlpatterns = [
    path('', views.home, name='home'),
    path('catalog/', views.product_list, name='product_list'),
    path('cart/', views.cart, name='cart'),
    path('products/<int:pk>/', views.product_detail, name='product_detail'),
    path('auth/register/', auth_views.register, name='register'),
    path('auth/login/', auth_views.login_view, name='login'),
    path('auth/logout/', auth_views.logout_view, name='logout'),
    path('auth/verify-email/', auth_views.email_verification_pending, name='email_verification_pending'),
    path('auth/verify-email/resend/', auth_views.resend_verification_email, name='resend_verification_email'),
    path('auth/verify-email/<uidb64>/<token>/', auth_views.verify_email, name='verify_email'),
    path('auth/forgot-password/', auth_views.AppPasswordResetView.as_view(), name='password_reset'),
    path('auth/forgot-password/sent/', auth_views.AppPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('auth/reset/<uidb64>/<token>/', auth_views.AppPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('auth/reset/complete/', auth_views.AppPasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('account/dashboard/', auth_views.dashboard, name='dashboard'),
    path('account/settings/', auth_views.profile_settings, name='profile_settings'),
    path('account/moderator/', auth_views.moderator_console, name='moderator_console'),
    path('account/access-denied/', auth_views.access_denied, name='access_denied'),
    path('account/change-password/', auth_views.change_password, name='change_password'),
]
