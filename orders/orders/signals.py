from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.dispatch import receiver, Signal
from django_rest_passwordreset.signals import reset_password_token_created
from backend.models import ConfirmEmailToken, User

new_user_registered = Signal()
new_order = Signal()


@receiver(reset_password_token_created)
def password_reset_token_created(sender, instance, reset_password_token, **kwargs):
    # сброс пароля посредством почты
    msg = EmailMultiAlternatives(f"Сброс токена почты для пользователя {reset_password_token.user}",
                                 reset_password_token.key, settings.EMAIL_HOST_USER,
                                 [reset_password_token.user.email])
    msg.send()


@receiver(new_user_registered)
def new_user_registered_signal(user_id, **kwargs):
    # письмо на указанную при регистрации почту с подтверждением
    token, _ = ConfirmEmailToken.objects.get_or_create(user_id=user_id)
    msg = EmailMultiAlternatives(f"Токен успешно зарегистрирован для почты {token.user.email}",
                                 token.key, settings.EMAIL_HOST_USER, [token.user.email])
    msg.send()


@receiver(new_order)
def new_order_signal(user_id, **kwargs):
    # отправить письмо об изменении статуса заказа
    user = User.objects.get(id=user_id)
    msg = EmailMultiAlternatives("Спасибо за сделанный Вами заказ!",
                                 f'Номер вашего заказа: {kwargs["order_id"]}\n'
                                 f'Мы свяжемся с Вами для уточнения деталей заказа в ближайшее время.'
                                 f'Статус Ваших заказов вы можете в любое время посмотреть в разделе "Заказы"',
                                 settings.EMAIL_HOST_USER, [user.email])
    msg.send()
