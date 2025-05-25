from django.contrib import admin
from .models import Product, CartItem, WishlistItem, Order, OrderItem
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from .models import ProductAttribute,ProductAttributeValue,ProductVariant

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

# admin.site.unregister(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at', 'status', 'payment_method')
    list_filter = ('status', 'payment_method')
    search_fields = ('user__username', 'id')
    list_editable = ('status',)  # make status editable directly in list view

# admin.site.unregister(Order)
# admin.site.register(Order, OrderAdmin)


@admin.action(description='Cancel selected orders')
def cancel_orders(modeladmin, request, queryset):
    for order in queryset:
        if order.status != 'Cancelled':
            order.status = 'Cancelled'
            order.save()
            send_mail(
                subject=f'Latta Clothing Store: Order #{order.id} Cancelled',
                message=(
                f"Dear {order.user.first_name or order.user.username},\n\n"
                f"We regret to inform you that your order #{order.id}, placed on {order.created_at.strftime('%B %d, %Y')}, "
                f"has been cancelled by our team.\n\n"
                f"If you have any questions or believe this was a mistake, feel free to contact our support team.\n\n"
                f"Order Details:\n"
                f" - Order ID: {order.id}\n"
                f" - Total Amount: NPR {order.total_price}\n"
                f" - Payment Method: {order.get_payment_method_display()}\n"
                f" - Status: Cancelled\n\n"
                f"Thank you for using Latta Clothing Store.\n"
                f"Best regards,\n"
                f"Latta Clothing Store Team"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.user.email],
            fail_silently=True,
            )

def send_delivery_notification(order):
    subject = 'Your Hamro Store Order Has Been Delivered!'
    message = f"""
    Hi {order.user.username},

    We're happy to inform you that your order #{order.id} has been delivered successfully.

    Thank you for shopping with us!

    Regards,
    Latta Clothing Store Team
    """
    recipient_list = [order.user.email]
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list)




# admin.site.register(Order, OrderAdmin)


# Register other models with default admin
admin.site.register(Product)
admin.site.register(ProductAttribute)
admin.site.register(ProductAttributeValue)
admin.site.register(ProductVariant)
# admin.site.register(CartItem)
# admin.site.register(WishlistItem)

