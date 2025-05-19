from django.contrib import admin

from .models import Product, CartItem, WishlistItem, Order, OrderItem

from django.core.mail import send_mail
from django.conf import settings


# Register your models here.
# admin.site.register(Product)


# Customize Order admin
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_price', 'status', 'created_at')
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('user__username', 'full_name', 'phone')
    readonly_fields = ('created_at', 'total_price')
    ordering = ('-created_at',)
    list_editable = ('status',)
    date_hierarchy = 'created_at'

# Customize OrderItem admin
@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'price')
    list_filter = ('product',)
    search_fields = ('order__user__username', 'product__name')



@admin.action(description='Cancel selected orders')
def cancel_orders(modeladmin, request, queryset):
    for order in queryset:
        if order.status != 'Cancelled':
            order.status = 'Cancelled'
            order.save()

            # Send email notification to the user
            send_mail(
                subject='Order Cancelled',
                message=f'Hi {order.user.username},\n\nYour order #{order.id} has been cancelled by admin.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[order.user.email],
                fail_silently=True,
            )

class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at', 'total_price', 'status', 'payment_method')
    list_filter = ('status', 'payment_method')
    actions = [cancel_orders]

admin.site.register(Order, OrderAdmin)


# Register other models with default admin
# admin.site.register(Product)
# admin.site.register(CartItem)
# admin.site.register(WishlistItem)

