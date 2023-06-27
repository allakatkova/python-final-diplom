from rest_framework import serializers
from backend.models import Shop, Contact, User, Category, Product, ShopProduct, Parameter, ProductInf
from rest_framework.exceptions import ValidationError
import re


class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ('id', 'name', 'state', 'seller', 'is_work', 'file')
        read_only_fields = ('id',)
