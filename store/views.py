from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.http import JsonResponse
from decimal import Decimal, ROUND_HALF_UP
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from django.contrib import messages

from store.forms import CustomUserCreationForm
from .models import Product, Order, OrderItem, WishlistItem
import stripe
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.http import HttpResponse
from io import BytesIO
from django.core.mail import send_mail
from django.conf import settings






stripe.api_key = settings.STRIPE_SECRET_KEY


def home(request):
    """Display available products on homepage."""
    products = Product.objects.filter(is_available=True)
    return render(request, 'store/home.html', {'products': products})


def add_to_cart(request, product_id):
    """Add a product to the cart stored in session."""
    cart = request.session.get('cart', {})
    product_id = str(product_id)
    product = get_object_or_404(Product, pk=product_id)

    # Remove from wishlist if present
    WishlistItem.objects.filter(user=request.user, product_id=product_id).delete()

    if product_id in cart:
        cart[product_id]['quantity'] += 1
    else:
        cart[product_id] = {
            'name': product.name,
            'price': float(product.price),  # store price as float for JSON serializability
            'quantity': 1
        }

    request.session['cart'] = cart

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # Return JSON response for AJAX calls
        return JsonResponse({
            'message': 'Product added to cart',
            'cartCount': len(cart),
            'productName': product.name,
            'price': float(product.price),
        })

    return redirect('view_cart')


def view_cart(request):
    """Show all cart items with total price."""
    cart = request.session.get('cart', {})
    cart_items = []
    total = 0

    for product_id, item in cart.items():
        product = get_object_or_404(Product, id=product_id)
        item_total = float(item['price']) * item['quantity']
        total += item_total
        cart_items.append({
            'product': product,
            'quantity': item['quantity'],
            'total': item_total,
        })

    # Save total in session for Stripe checkout
    request.session['cart_total'] = total

    return render(request, 'store/cart.html', {'cart_items': cart_items, 'total': total})


def remove_from_cart(request, product_id):
    """Remove a product from the cart."""
    cart = request.session.get('cart', {})
    if str(product_id) in cart:
        del cart[str(product_id)]
    request.session['cart'] = cart
    return redirect('view_cart')


def update_cart(request, product_id, action):
    """Increase or decrease quantity of a cart item."""
    cart = request.session.get('cart', {})
    product_id = str(product_id)

    if product_id in cart:
        if action == "increase":
            cart[product_id]['quantity'] += 1
        elif action == "decrease":
            cart[product_id]['quantity'] -= 1
            if cart[product_id]['quantity'] <= 0:
                del cart[product_id]

    request.session['cart'] = cart
    return redirect('view_cart')


@login_required
def add_to_wishlist(request, product_id):
    """Add product to user's wishlist."""
    product = get_object_or_404(Product, id=product_id)
    wishlist_item, created = WishlistItem.objects.get_or_create(user=request.user, product=product)
    message = "Added to wishlist" if created else "Already in wishlist"
    wishlist_count = WishlistItem.objects.filter(user=request.user).count()
    return JsonResponse({'message': message, 'wishlistCount': wishlist_count, 'productName': product.name})


@login_required
def remove_from_wishlist(request, product_id):
    """Remove product from user's wishlist."""
    product = get_object_or_404(Product, id=product_id)
    WishlistItem.objects.filter(user=request.user, product=product).delete()
    wishlist_count = WishlistItem.objects.filter(user=request.user).count()
    return JsonResponse({'message': "Removed from wishlist", 'wishlistCount': wishlist_count, 'productName': product.name})


def wishlist_view(request):
    """Display logged-in user's wishlist."""
    if not request.user.is_authenticated:
        messages.info(request, "Please log in to view your wishlist.")
        return redirect('login')
    items = WishlistItem.objects.filter(user=request.user).select_related('product')
    return render(request, 'store/wishlist.html', {'wishlist_items': items})


# def register(request):
#     """User registration view."""
#     if request.user.is_authenticated:
#         return redirect('home')

#     if request.method == 'POST':
#         form = UserCreationForm(request.POST)
#         if form.is_valid():
#             user = form.save()
#             login(request, user)
#             return redirect('home')
#     else:
#         form = UserCreationForm()

#     return render(request, 'store/register.html', {'form': form})
def register(request):
    """Enhanced user registration view with email support."""
    if request.user.is_authenticated:
        messages.info(request, "You're already logged in!")
        return redirect('home')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)  # Use custom form
        if form.is_valid():
            user = form.save()
            
            # Log the user in automatically
            login(request, user)
            
            # Send welcome email
            send_mail(
                subject="Welcome to Our Store!",
                message=f"Hi {user.username},\n\nThanks for registering with us!",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True
            )
            
            messages.success(request, "Registration successful! Welcome!")
            return redirect('home')
    else:
        form = CustomUserCreationForm()

    return render(request, 'store/register.html', {
        'form': form,
        'title': 'Create Account'
    })


# class UserRegisterView(CreateView):
#     """Class-based user registration view."""
#     form_class = UserCreationForm
#     template_name = 'store/register.html'
#     success_url = reverse_lazy('login')

#     def form_valid(self, form):
#         user = form.save(commit=False)
#         user.is_staff = False
#         user.is_superuser = False
#         user.save()
#         return super().form_valid(form)

class UserRegisterView(CreateView):
    """Enhanced class-based registration view with email support."""
    form_class = CustomUserCreationForm  # Using custom form
    template_name = 'store/register.html'
    success_url = reverse_lazy('home')  # Redirect to home after registration
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, "You're already logged in!")
            return redirect(self.success_url)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        user = form.instance
        
        # Log the user in after registration
        login(self.request, user)
        
        # Send welcome email
        send_mail(
            subject="Welcome to Our Store!",
            message=f"Hi {user.username},\n\nThanks for registering with us!",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True
        )
        
        messages.success(self.request, "Registration successful! Welcome!")
        return response


@login_required
def checkout(request):
    """Process checkout form and create order."""
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        payment_method = request.POST.get('payment_method')
        cart = request.session.get('cart', {})

        if not cart:
            return redirect('view_cart')

        total_price = 0
        for item in cart.values():
            total_price += Decimal(item['price']) * item['quantity']

        order = Order.objects.create(
            user=request.user,
            full_name=full_name,
            phone=phone,
            address=address,
            total_price=total_price,
            payment_method=payment_method,
        )

        for product_id, item in cart.items():
            OrderItem.objects.create(
                order=order,
                product_id=product_id,
                quantity=item['quantity'],
                price=item['price'],
            )

        # Clear cart after order creation
        request.session['cart'] = {}

        if payment_method == 'stripe':
            # Save order ID in session for payment confirmation
            request.session['order_id'] = order.id
            return redirect('create_checkout_session')

        # If Cash on Delivery (COD)
        return redirect('order_success')

    return render(request, 'store/checkout.html')


def create_checkout_session(request):
    """Create Stripe checkout session and redirect user to payment page."""
    order_id = request.session.get('order_id')
    if not order_id:
        return redirect('checkout')

    order = get_object_or_404(Order, id=order_id)
    
    # Convert total price to paisa with proper rounding
    total_amount = int((order.total_price * Decimal('100')).quantize(Decimal('1'), rounding=ROUND_HALF_UP))

    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'npr',
                'product_data': {
                    'name': f'Hamro Store Order #{order.id}',
                },
                'unit_amount': total_amount,
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url=request.build_absolute_uri(reverse_lazy('order_success')),
        cancel_url=request.build_absolute_uri(reverse_lazy('checkout')),
    )

    return redirect(session.url)


def order_success(request):
    """Render order success page after successful payment or COD."""
    return render(request, 'store/order_success.html')


@login_required
def my_orders(request):
    """Display all orders placed by the logged-in user."""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'store/my_orders.html', {'orders': orders})

@login_required
def order_detail(request, order_id):
    """Show details for a specific order."""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'store/order_detail.html', {'order': order})


@login_required
def download_invoice(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    template = get_template('store/invoice.html')
    html = template.render({'order': order})

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_order_{order.id}.pdf"'

    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('Failed to generate PDF', status=500)
    return response
@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if order.status == 'Pending':
        order.status = 'Cancelled'
        order.save()
        
        # Send cancellation email
        subject = f'Order #{order.id} Cancelled'
        message = (
            f"Hello {order.full_name},\n\n"
            f"Your order #{order.id} has been successfully cancelled.\n\n"
            f"If you have any questions, please contact us.\n\n"
            f"Thank you,\nLatta Clothing Team"
        )
        recipient_list = [order.user.email]
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list)
        
        messages.success(request, 'Your order has been cancelled. A confirmation email has been sent.')
    else:
        messages.warning(request, 'Order cannot be cancelled.')

    return redirect('order_detail', order_id=order.id)



