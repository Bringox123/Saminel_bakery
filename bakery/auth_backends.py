from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q


class EmailOrUsernameBackend(ModelBackend):
    """Authenticate users using either username or email."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        identifier = username or kwargs.get('email')
        if not identifier or not password:
            return None

        user_model = get_user_model()
        user = None

        try:
            user = user_model.objects.get(
                Q(username__iexact=identifier) | Q(email__iexact=identifier)
            )
        except user_model.DoesNotExist:
            user_model().set_password(password)
            return None
        except user_model.MultipleObjectsReturned:
            user = user_model.objects.filter(email__iexact=identifier).order_by('id').first()

        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
