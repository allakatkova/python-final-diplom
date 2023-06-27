from rest_framework import serializers
from backend.models import Shop, Contact, User, Category, Product, ShopProduct, Parameter, ProductInf
from rest_framework.exceptions import ValidationError
import re


class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ('id', 'name', 'state', 'seller', 'is_work', 'file')
        read_only_fields = ('id',)


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ('id', 'country', 'region', 'zip', 'city', 'street',
                  'house', 'building', 'apartment', 'phone', 'user')
        read_only_fields = ('id',)
        extra_kwargs = {
            'user': {'write_only': True}
        }

    def validate(self, attrs):
        if attrs['phone']:
            if re.search(r"((8|\+7)[\- ]?)?(\(?\d{3}\)?[\- ]?)?[\d\- ]{7,10}", attrs['phone']) is not None:
                return attrs
            else:
                raise ValidationError(
                    {'Status': False, 'Errors': "Неверный формат номера"})
        if attrs['zip']:
            if len(attrs['zip']) <= 10 & attrs['zip'] is not None:
                return attrs
            else:
                raise ValidationError(
                    {'Status': False, 'Errors': "Неверный формат почтового индекса"})


class UserSerializer(serializers.ModelSerializer):
    contacts = ContactSerializer(read_only=True, many=True)

    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'email',
                  'company', 'position', 'contacts', 'password', 'type')
        read_only_fields = ('id',)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name')
        read_only_fields = ('id',)


class ShopSerializer(serializers.ModelSerializer):
    seller = UserSerializer()

    class Meta:
        model = Shop
        fields = ('id', 'name', 'seller', 'url', 'is_work')
        read_only_fields = ('id',)


class ParameterSerializers(serializers.ModelSerializer):
    class Meta:
        model = Parameter
        fields = ('id', 'name')
        read_only_fields = ('id',)


class ProductInfSerializer(serializers.ModelSerializer):
    parameter = ParameterSerializers()

    class Meta:
        model = ProductInf
        fields = ('parameter', 'value')
        read_only_fields = ('id',)


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer()
    product_inf = ProductInfSerializer(many=True)

    class Meta:
        model = Product
        fields = ('id', 'model', 'name', 'category', 'product_inf')
        read_only_fields = ('id',)


class ShopProductSerializer(serializers.ModelSerializer):
    shop = ShopSerializer()
    product = ProductSerializer()

    class Meta:
        model = ShopProduct
        fields = ('id', 'shop', 'product', 'ext_id',
                  'quantity', 'price', 'price_rrc')
        read_only_fields = ('id',)
