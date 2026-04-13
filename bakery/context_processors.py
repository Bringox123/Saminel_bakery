from django.conf import settings


def auth_feature_flags(request):
    return {
        'google_social_login_enabled': getattr(settings, 'GOOGLE_SOCIAL_LOGIN_ENABLED', False),
    }
