from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views import UserRegisterView, CustomLoginView

urlpatterns = [
    path('', views.home, name='home'),

    # Cart URLs
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.view_cart, name='view_cart'),
    path('remove-from-cart/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('update-cart/<int:product_id>/<str:action>/', views.update_cart, name='update_cart'),

    # Wishlist URLs
    path('add-to-wishlist/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('remove-from-wishlist/<int:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('wishlist/', views.wishlist_view, name='wishlist'),

    # User authentication URLs
    path('register/', UserRegisterView.as_view(), name='register'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),

    # Checkout and payment URLs
    path('checkout/', views.checkout, name='checkout'),
    path('create-checkout-session/', views.create_checkout_session, name='create_checkout_session'),
    path('order/success/', views.order_success, name='order_success'),
    path('my-orders/', views.my_orders, name='my_orders'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    path('my-orders/<int:order_id>/invoice/', views.download_invoice, name='download_invoice'),
    path('my-orders/<int:order_id>/cancel/', views.cancel_order, name='cancel_order'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('filter-products/', views.filter_products, name='filter_products'),

    # Additional info pages
    path('about/', views.about, name='about'),
    path('terms/', views.terms, name='terms'),
    path('privacy/', views.privacy, name='privacy'),
]
