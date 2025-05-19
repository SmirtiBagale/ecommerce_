from django.db import models
from django.contrib.auth.models import User


class Product(models.Model):
    """
    Represents a product in the store.
    """
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='product_images/')
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class CartItem(models.Model):
    """
    Item in a user's cart.
    Stores the quantity of each product added to the cart by a user.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product.name} for {self.user.username}"


class WishlistItem(models.Model):
    """
    Represents a product saved by a user in their wishlist.
    Unique constraint ensures no duplicate wishlist entries per user/product.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"


class Order(models.Model):
    """
    Represents a user's order, storing details including
    shipping info, total price, order status, and payment method.
    """
    PAYMENT_CHOICES = (
        ('cod', 'Cash on Delivery'),
        ('stripe', 'Stripe'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    full_name = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)

    status = models.CharField(max_length=20, default='Pending')  # e.g., Pending, Completed

    payment_method = models.CharField(
        max_length=10,
        choices=PAYMENT_CHOICES,
        default='cod',
    )

    def __str__(self):
        return f"Order {self.id} by {self.user.username}"


class OrderItem(models.Model):
    """
    Individual product entry in an order, with quantity and price
    (price captured at time of purchase).
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price at purchase time

    def __str__(self):
        return f"{self.quantity} of {self.product.name}"
    


