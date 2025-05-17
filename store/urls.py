from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .views import UserRegisterView



urlpatterns = [
    path('', views.home, name='home'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.view_cart, name='view_cart'),
    path('remove-from-cart/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),

   
    path('update-cart/<int:product_id>/<str:action>/', views.update_cart, name='update_cart'),
    path('add-to-wishlist/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('remove-from-wishlist/<int:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('register/', UserRegisterView.as_view(), name='register'),

    path('login/', auth_views.LoginView.as_view(template_name='store/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('checkout/', views.checkout, name='checkout'),
     path("verify-khalti-payment/", views.verify_khalti_payment, name="verify_khalti_payment"),

]
