from django.conf import settings
from django.contrib.auth import logout
from django.utils import timezone


class InactivityLogoutMiddleware:
    """Log out authenticated users after prolonged inactivity."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        timeout_seconds = int(getattr(settings, 'AUTH_IDLE_TIMEOUT_SECONDS', 0) or 0)

        if timeout_seconds > 0 and request.user.is_authenticated:
            current_ts = timezone.now().timestamp()
            last_ts = request.session.get('last_activity_ts')

            if last_ts and (current_ts - float(last_ts) > timeout_seconds):
                logout(request)
                request.session['session_timed_out'] = True
            request.session['last_activity_ts'] = current_ts

        return self.get_response(request)
