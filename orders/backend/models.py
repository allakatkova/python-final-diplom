from django.db import models
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.validators import UnicodeUsernameValidator
import django_rest_passwordreset.tokens

USER_TYPE_CHOICES = (
    ('seller', 'Продавец'),
    ('buyer', 'Покупатель'),
)

STATE_CHOICES = (
    ('basket', 'В корзине'),
    ('new', 'Новый'),
    ('confirmed', 'Подтвержден'),
    ('assembled', 'Собран'),
    ('sent', 'Отправлен'),
    ('delivered', 'Доставлен'),
    ('canceled', 'Отменен'),
)


class CustomUser(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """
        Create and save a user with the given username, email, and password.
        """
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    object = CustomUser()
    email = models.EmailField(_('email adress'), unique=True)
    company = models.CharField(
        verbose_name='Компания', max_length=64, blank=True)
    position = models.CharField(
        verbose_name='Должность', max_length=32, blank=True)
    username_validator = UnicodeUsernameValidator()
    username = models.CharField(_('username'),
                                max_length=128,
                                help_text=_(
                                    'Required. 128 characters or fewer. Letters, digits and @/./+/-/_ only.'),
                                validators=[username_validator],
                                error_messages={
                                    'unique': _("A user with that username already exists."),
    })
    is_active = models.BooleanField(_('active'),
                                    default=False,
                                    help_text=_(
                                        'Designates whether this user should be treated as active. '
                                        'Unselect this instead of deleting accounts.'
    ))
    type = models.CharField(verbose_name='Тип пользователя',
                            choices=USER_TYPE_CHOICES, max_length=16, default='buyer')

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Список пользователей'
        ordering = ('email',)


class Shop(models.Model):
    name = models.CharField(
        max_length=64, verbose_name='Название магазина', unique=True)
    url = models.URLField(blank=True, null=True, verbose_name='Ссылка')
    seller = models.OneToOneField(User, verbose_name='Продавец', blank=True, null=True,
                                  on_delete=models.CASCADE)
    is_work = models.BooleanField(verbose_name='Доступность', default=True)

    class Meta:
        verbose_name = 'Магазин'
        verbose_name_plural = 'Магазины'
        ordering = ('-name',)

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=32, verbose_name='Название категории')
    id = models.PositiveIntegerField(
        verbose_name='ИД категории', primary_key=True)
    shops = models.ManyToManyField(
        Shop, verbose_name='Магазины', related_name='categories', blank=True)

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Список категорий'
        ordering = ('-name',)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=64, verbose_name='Название продукта')
    model = models.CharField(max_length=64, verbose_name='Модель', blank=True)
    category = models.ForeignKey(Category, verbose_name='Категория', related_name='products', blank=True,
                                 null=True, on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = "Список продуктов"
        ordering = ('-name',)

    def __str__(self):
        return self.name


class ShopProduct(models.Model):
    shop = models.ForeignKey(Shop, verbose_name='Магазин', related_name='product_in_shop', blank=True,
                             on_delete=models.CASCADE)
    product = models.ForeignKey(Product, verbose_name='Товар', related_name='product_in_shop', blank=True,
                                on_delete=models.CASCADE)
    ext_id = models.PositiveIntegerField(verbose_name='Внешний ИД')
    quantity = models.PositiveIntegerField(verbose_name='Количество')
    price = models.PositiveIntegerField(verbose_name='Цена')
    price_rrc = models.PositiveIntegerField(
        verbose_name='Рекомендованная розничная цена')

    class Meta:
        verbose_name = 'Продукт в магазине'
        verbose_name_plural = 'Список продуктов в магазине'


class Parameter(models.Model):
    name = models.CharField(max_length=64, verbose_name='Название')

    class Meta:
        verbose_name = 'Название парамметра'
        verbose_name_plural = 'Список парамметров'
        ordering = ('-name',)

    def __str__(self):
        return self.name


class ProductInf(models.Model):
    product = models.ForeignKey(Product, verbose_name='Товар', related_name='product_inf', blank=True,
                                null=True, on_delete=models.CASCADE)
    parameter = models.ForeignKey(Parameter, verbose_name='Параметр', related_name='product_inf', blank=True,
                                  on_delete=models.CASCADE)
    value = models.CharField(
        max_length=128, blank=True, verbose_name='Значение')

    class Meta:
        verbose_name = 'Информация о продукте'
        verbose_name_plural = 'Список информации о продуктах'


class Contact(models.Model):
    user = models.ForeignKey(User, verbose_name='Пользователь', related_name='contacts', blank=True,
                             on_delete=models.CASCADE)
    country = models.CharField(max_length=64, verbose_name='Страна')
    region = models.CharField(max_length=64, verbose_name='Регион')
    zip = models.IntegerField(verbose_name='Почтовый индекс')
    city = models.CharField(max_length=64, verbose_name='Город')
    street = models.CharField(max_length=128, verbose_name='Улица')
    house = models.CharField(max_length=16, verbose_name='Дом', null=True)
    building = models.CharField(
        max_length=16, verbose_name='Строение', null=True)
    apartment = models.CharField(
        max_length=16, verbose_name='Квартира', null=True)
    phone = models.CharField(max_length=32, verbose_name='Телефон')

    class Meta:
        verbose_name = 'Контакты пользователя'
        verbose_name_plural = "Список контактов пользователя"


class Order(models.Model):
    user = models.ForeignKey(User, verbose_name='Пользователь', related_name='orders',
                             blank=True, on_delete=models.CASCADE)
    dt = models.DateTimeField(auto_now_add=True)
    state = models.CharField(verbose_name='Статус заказа',
                             choices=STATE_CHOICES, max_length=16)
    user_contact = models.ForeignKey(Contact, verbose_name='Контакты', blank=True, null=True,
                                     on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Список заказов'
        ordering = ('-dt',)

    def __str__(self):
        return str(self.dt)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, verbose_name='Заказ', related_name='ordered_items', blank=True,
                              on_delete=models.CASCADE)
    product_info = models.ForeignKey(ProductInf, verbose_name='Информация о продукте', related_name='ordered_items',
                                     blank=True, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(verbose_name='Количество')

    class Meta:
        verbose_name = 'Заказанная позиция'
        verbose_name_plural = 'Список заказанных позиций'


class ShopFiles(models.Model):
    file = models.FileField(null=True, upload_to='uploaded_data')
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, null=True)


class ConfirmEmailToken(models.Model):
    class Meta:
        verbose_name = 'Токен подтверждения Email'
        verbose_name_plural = 'Токены подтверждения Email'

    @staticmethod
    def generate_key():
        """ generates a pseudo random code using os.urandom and binascii.hexlify """
        return django_rest_passwordreset.tokens.get_token_generator().generate_token()

    user = models.ForeignKey(
        User,
        related_name='confirm_email_tokens',
        on_delete=models.CASCADE,
        verbose_name=_(
            "The User which is associated to this password reset token")
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("When was this token generated")
    )

    # Key field, though it is not the primary key of the model
    key = models.CharField(
        _("Key"),
        max_length=64,
        db_index=True,
        unique=True
    )

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        return super(ConfirmEmailToken, self).save(*args, **kwargs)

    def __str__(self):
        return "Password reset token for user {user}".format(user=self.user)
