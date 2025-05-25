from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class ProductAttribute(models.Model):
    """
    Defines attributes like Size, Color, Material etc.
    """
    name = models.CharField(max_length=50)  # e.g., "Size", "Color"
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class ProductAttributeValue(models.Model):
    """
    Specific values for attributes (e.g., "Red", "Blue" for Color)
    """
    attribute = models.ForeignKey(ProductAttribute, on_delete=models.CASCADE)
    value = models.CharField(max_length=100)  # e.g., "XL", "Red"
    
    class Meta:
        ordering = ['attribute__name', 'value']
        unique_together = ('attribute', 'value')

    def __str__(self):
        return f"{self.attribute.name}: {self.value}"


class Product(models.Model):
    """
    Represents a product in the store with base information.
    """
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    base_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
      
        help_text="Base price without variations"
    )
    image = models.ImageField(upload_to='product_images/')
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    attributes = models.ManyToManyField(
        ProductAttribute,
        blank=True,
        help_text="Attributes available for this product"
    )

    class Meta:
        ordering = ['-created_at']

    @property
    def price(self):
        """Dynamic price showing cheapest variant or base price"""
        if hasattr(self, 'variants') and self.variants.filter(is_active=True).exists():
            return min(v.get_final_price() for v in self.variants.filter(is_active=True))
        return self.base_price

    def __str__(self):
        return self.name


class ProductVariant(models.Model):
    """
    Represents a specific variant of a product with unique SKU, price, and stock
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    sku = models.CharField(max_length=50, unique=True)
    price_modifier = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=0.00,
        help_text="Additional price over base product price"
    )
    stock = models.PositiveIntegerField(default=0)
    attributes = models.ManyToManyField(ProductAttributeValue)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['product__name', 'sku']

    def get_final_price(self):
        return self.product.base_price + self.price_modifier

    def get_attributes_display(self):
        return ", ".join([str(attr) for attr in self.attributes.all()])

    def __str__(self):
        return f"{self.product.name} - {self.get_attributes_display()}"


class CartItem(models.Model):
    """
    Item in a user's cart with variant support.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Selected variant if applicable"
    )
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product', 'variant')
        ordering = ['-added_at']

    def get_item_price(self):
        return self.variant.get_final_price() if self.variant else self.product.price

    def get_total_price(self):
        return self.get_item_price() * self.quantity

    def __str__(self):
        variant_info = f" ({self.variant})" if self.variant else ""
        return f"{self.quantity} x {self.product.name}{variant_info}"


class WishlistItem(models.Model):
    """
    Represents a product saved by a user in their wishlist.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')
        ordering = ['-added_at']

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"


class Order(models.Model):
    """
    Represents a user's order with status tracking.
    """
    PAYMENT_CHOICES = (
        ('cod', 'Cash on Delivery'),
        ('stripe', 'Stripe'),
    )

    ORDER_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Processing', 'Processing'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    # Shipping information
    full_name = models.CharField(max_length=100)
    address = models.TextField()
    phone = models.CharField(max_length=20)

    status = models.CharField(
        max_length=20,
        choices=ORDER_STATUS_CHOICES,
        default='Pending'
    )
    payment_method = models.CharField(
        max_length=10,
        choices=PAYMENT_CHOICES,
        default='cod',
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order {self.id} by {self.user.username}"


class OrderItem(models.Model):
    """
    Individual product entry in an order with variant support.
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Variant purchased if applicable"
    )
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price at purchase time

    class Meta:
        ordering = ['order']

    def get_total_price(self):
        return self.price * self.quantity

    def __str__(self):
        variant_info = f" ({self.variant})" if self.variant else ""
        return f"{self.quantity} of {self.product.name}{variant_info}"


class Review(models.Model):
    """
    Product reviews with variant-specific feedback option.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Specific variant being reviewed if applicable"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('product', 'user', 'variant')  # One review per product/variant per user
        ordering = ['-created_at']

    def __str__(self):
        variant_info = f" ({self.variant})" if self.variant else ""
        return f"{self.user.username} - {self.product.name}{variant_info} ({self.rating})"