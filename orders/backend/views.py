from django.shortcuts import render
from .forms import UploadFileForm
from django.http import JsonResponse
from rest_framework.views import APIView
from backend.models import Shop, ShopFiles, Category, Product, ShopProduct, Parameter, ProductInf, ConfirmEmailToken, Contact, User
import yaml
from orders.settings import BASE_DIR, DATA_ROOT
import os
from django.contrib.auth.password_validation import validate_password
from backend.serializers import UserSerializer, CategorySerializer, ShopSerializer, ProductSerializer, ShopProductSerializer, ProductInfSerializer, ContactSerializer
from backend.signals import new_user_registered, new_order
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from rest_framework.viewsets import ModelViewSet
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Sum, F


class RegisterAccount(APIView):
    def post(self, request, *args, **kwargs):
        if {'first_name', 'last_name', 'email', 'password', 'company', 'position', 'type'}.issubset(request.data):
            errors = {}
            try:
                validate_password(request.data['password'])
            except Exception as password_error:
                error_array = []
                for item in password_error:
                    error_array.append(item)
                return JsonResponse({'Status': False, 'Errors': {'password': error_array}})
            else:
                user_serializer = UserSerializer(data=request.data)
                # проверка уникальности имени пользователя и его сохранение
                if user_serializer.is_valid():
                    user = user_serializer.save()
                    user.set_password(request.data['password'])
                    user.save()
                    new_user_registered.send(
                        sender=self.__class__, user_id=user.id)
                    return JsonResponse({'Status': True})
                else:
                    return JsonResponse({'Status': False, 'Errors': user_serializer.errors})
        return JsonResponse({'Status': False, 'Errors': 'Необходимо указать все требуемые аргументы'})


class ConfirmAccount(APIView):
    def post(self, request, *args, **kwargs):
        if {'email', 'token'}.issubset(request.data):
            token = ConfirmEmailToken.objects.filter(
                user__email=request.data['email'], key=request.data['token']).first()
            if token:
                token.user.is_active = True
                token.user.save()
                token.delete()
                return JsonResponse({'Status': True})
            else:
                return JsonResponse({'Status': False, 'Errors': 'Проверьте правильность написания аргументов email или токен'})
        return JsonResponse({'Status': False, 'Errors': 'Необходимо указать все требуемые аргументы'})


class AccountDetails(APIView):
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)
        else:
            serializer = UserSerializer(request.user)
            return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)
        if 'password' in request.data:
            errors = {}
            # проверка пароля на сложность
            try:
                validate_password(request.data['password'])
            except Exception as password_error:
                error_array = []
                for item in password_error:
                    error_array.append(item)
                return JsonResponse({'Status': False, 'Errors': {'password': error_array}})
            else:
                request.user.set_password(request.data['password'])
        user_serializer = UserSerializer(
            request.user, data=request.data, partial=True)
        if user_serializer.is_valid():
            user_serializer.save()
            return JsonResponse({'Status': True})
        else:
            return JsonResponse({'Status': False, 'Errors': user_serializer.errors})


class LoginAccount(APIView):
    def post(self, request, *args, **kwargs):
        if {'email', 'password'}.issubset(request.data):
            user = authenticate(
                request, username=request.data['email'], password=request.data['password'])
            if user is not None:
                if user.is_active:
                    token, _ = Token.objects.get_or_create(user=user)
                    return JsonResponse({'Status': True, 'Token': token.key})
            return JsonResponse({'Status': False, 'Errors': 'Ошибка авторизации!'})
        return JsonResponse({'Status': False, 'Errors': 'Необходимо указать все требуемые аргументы'})


class ShopUpload(APIView):
    def post(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)
        if request.user.type != 'seller':
            return JsonResponse({'Status': False, 'Error': 'Вход только для магазинов'}, status=403)
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            file = request.FILES.popitem()
            self.handle_uploaded_file(os.path.join(
                DATA_ROOT, str(file[1][0])), request.user.id)
            return JsonResponse({'Status': True})
        else:
            return JsonResponse({'Status': False})

    def handle_uploaded_file(sefl, shop_file, user):
        shop = Shop()
        product = Product()
        parameter = Parameter()
        with open(shop_file, 'r', encoding='utf8') as stream:
            try:
                shop_data = yaml.safe_load(stream)
                shop.name = shop_data['shop']
                seller = User.objects.filter(id=user).first()
                shop.seller = seller
                shop.save()
                for category in shop_data['categories']:
                    category_object, _ = Category.objects.get_or_create(
                        id=category['id'], name=category['name'])
                    category_object.shops.add(shop)
                    category_object.save()
                for goods in shop_data['goods']:
                    category = Category.objects.get(id=goods['category'])
                    product_object, _ = Product.objects.get_or_create(name=goods['name'], model=goods['model'],
                                                                      category=category)
                    product_object.save()
                    prod_pk = Product.objects.filter(
                        name=goods['name']).first()
                    shopproduct_object, _ = ShopProduct.objects.get_or_create(
                        ext_id=goods['id'], quantity=goods['quantity'], price=goods['price'], price_rrc=goods['price_rrc'], product=prod_pk, shop=shop)
                    shopproduct_object.save()
                    for parameters, value in goods['parameters'].items():
                        parameter_object, _ = Parameter.objects.get_or_create(
                            name=parameters)
                        parameter_object.save()
                        param_obj_pk = Parameter.objects.filter(
                            name=parameters).first()
                        product_inf_object, _ = ProductInf.objects.get_or_create(
                            value=value, parameter=param_obj_pk, product=prod_pk)
                        product_inf_object.save()
            except yaml.YAMLError as exc:
                return JsonResponse({'Status': False, 'Error': str(exc)})


class UserContact(APIView):
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)
        contact = Contact.objects.filter(user_id=request.user.id)
        serializer = ContactSerializer(contact, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)
        if {'country', 'region', 'zip', 'city', 'street', 'house', 'phone'}.issubset(request.data):
            request.data.update({'user': request.user.id})
            serializer = ContactSerializer(data=request.data)

            if serializer.is_valid():
                serializer.save()
                return JsonResponse({'Status': True})
            else:
                JsonResponse({'Status': False, 'Errors': serializer.errors})

        return JsonResponse({'Status': False, 'Errors': 'Необходимо указать все требуемые аргументы'})

    def delete(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)
        items_sting = request.data.get('items')
        if items_sting:
            items_list = items_sting.split(',')
            query = Q()
            objects_deleted = False
            for contact_id in items_list:
                if contact_id.isdigit():
                    query = query | Q(user_id=request.user.id, id=contact_id)
                    objects_deleted = True
            if objects_deleted:
                deleted_count = Contact.objects.filter(query).delete()[0]
                return JsonResponse({'Status': True, 'Удалено объектов': deleted_count})
        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})

    def put(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)
        if 'id' in request.data:
            if request.data['id'].isdigit():
                contact = Contact.objects.filter(
                    id=request.data['id'], user_id=request.user.id).first()
                if contact:
                    serializer = ContactSerializer(
                        contact, data=request.data, partial=True)
                    if serializer.is_valid():
                        serializer.save()
                        return JsonResponse({'Status': True})
                    else:
                        JsonResponse(
                            {'Status': False, 'Errors': serializer.errors})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


class CategoryViewSet(ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    http_method_names = ['get', ]


class ShopViewSet(ModelViewSet):
    queryset = Shop.objects.all()
    serializer_class = ShopSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['name', 'is_work']
    http_method_names = ['get', ]


class ProductViewSet(ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'model']
    http_method_names = ['get', ]


class ShopProductViewSet(ModelViewSet):
    queryset = ShopProduct.objects.all()
    serializer_class = ShopProductSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['product__model', 'product__name']
    http_method_names = ['get', ]


class ProductInfViewSet(ModelViewSet):
    queryset = ProductInf.objects.all()
    serializer_class = ProductInfSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['product_inf_id__product_id__model',
                     'product_inf_id__product_id__name']
    http_method_names = ['get', ]


###################################################################################


class PartnerUpdate(APIView):
    """
    Класс для обновления прайса от поставщика
    """

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        if request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'Только для магазинов'}, status=403)

        url = request.data.get('url')
        if url:
            validate_url = URLValidator()
            try:
                validate_url(url)
            except ValidationError as e:
                return JsonResponse({'Status': False, 'Error': str(e)})
            else:
                stream = get(url).content

                data = load_yaml(stream, Loader=Loader)

                shop, _ = Shop.objects.get_or_create(
                    name=data['shop'], user_id=request.user.id)
                for category in data['categories']:
                    category_object, _ = Category.objects.get_or_create(
                        id=category['id'], name=category['name'])
                    category_object.shops.add(shop.id)
                    category_object.save()
                ProductInfo.objects.filter(shop_id=shop.id).delete()
                for item in data['goods']:
                    product, _ = Product.objects.get_or_create(
                        name=item['name'], category_id=item['category'])

                    product_info = ProductInfo.objects.create(product_id=product.id,
                                                              external_id=item['id'],
                                                              model=item['model'],
                                                              price=item['price'],
                                                              price_rrc=item['price_rrc'],
                                                              quantity=item['quantity'],
                                                              shop_id=shop.id)
                    for name, value in item['parameters'].items():
                        parameter_object, _ = Parameter.objects.get_or_create(
                            name=name)
                        ProductParameter.objects.create(product_info_id=product_info.id,
                                                        parameter_id=parameter_object.id,
                                                        value=value)

                return JsonResponse({'Status': True})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})
