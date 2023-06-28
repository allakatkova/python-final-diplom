"""orders URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from backend.views import ShopUpload, RegisterAccount, ConfirmAccount, LoginAccount, CategoryViewSet, ShopViewSet, ProductViewSet, ShopProductViewSet, ProductInfViewSet, UserContact
from rest_framework.routers import DefaultRouter


r = DefaultRouter()
r.register('categories', CategoryViewSet)
r.register('shops', ShopViewSet)
r.register('products', ProductViewSet)
r.register('products_in_shop', ShopProductViewSet)
r.register('product_inf', ProductInfViewSet)
urlpatterns = r.urls
urlpatterns += [path('admin/', admin.site.urls)]
urlpatterns += [path('shop/upload', ShopUpload.as_view(), name='shop-upload')]
urlpatterns += [path('user/register',
                     RegisterAccount.as_view(), name='user-register')]
urlpatterns += [path('user/register/confirm',
                     ConfirmAccount.as_view(), name='user-register-confirm')]
urlpatterns += [path('user/login', LoginAccount.as_view(), name='user-login')]
