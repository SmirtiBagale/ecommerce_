# store/signals.py
from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Order
from django.core.mail import send_mail
from django.conf import settings

@receiver(pre_save, sender=Order)
def send_shipment_email(sender, instance, **kwargs):
    if not instance.pk:
        return  # new order, no status yet

    previous = Order.objects.get(pk=instance.pk)
    if previous.status != instance.status and instance.status == 'Shipped':
        subject = f"Your Latta Clothing Store Order #{instance.id} has been Shipped!"
        message = f"""
Dear {instance.user.username},

Your order #{instance.id} has been shipped!

Order Details:
{chr(10).join([f"- {item.product.name} (x{item.quantity})" for item in instance.items.all()])}

Shipping To:
{instance.full_name}
{instance.address}
Phone: {instance.phone}

You will be notified again once it is delivered.
Thank you for shopping with Latta Clothing Store!

Regards,
Latta Clothing Store Team
"""
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [instance.user.email],
            fail_silently=False
        )
