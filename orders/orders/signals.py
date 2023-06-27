from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.dispatch import receiver, Signal
from django_rest_passwordreset.signals import reset_password_token_created
from backend.models import ConfirmEmailToken, User

new_user_registered = Signal()
new_order = Signal()
