import re

from django.core.exceptions import ValidationError


class StrongPasswordValidator:
    """Require a balanced password with upper/lower/digit/symbol characters."""

    def validate(self, password, user=None):
        if len(password) < 10:
            raise ValidationError('Password must be at least 10 characters long.')
        if not re.search(r'[A-Z]', password):
            raise ValidationError('Password must include at least one uppercase letter.')
        if not re.search(r'[a-z]', password):
            raise ValidationError('Password must include at least one lowercase letter.')
        if not re.search(r'\d', password):
            raise ValidationError('Password must include at least one number.')
        if not re.search(r'[^A-Za-z0-9]', password):
            raise ValidationError('Password must include at least one symbol.')

    def get_help_text(self):
        return (
            'Your password must be at least 10 characters and include uppercase, '
            'lowercase, number, and symbol characters.'
        )
