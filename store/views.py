from django.shortcuts import render, redirect, get_object_or_404

from django.http import JsonResponse
from decimal import Decimal
from django.contrib.auth.decorators import login_required


from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login

from django.urls import reverse_lazy
from django.views.generic.edit import CreateView

from django.contrib import messages


from .models import Product, Order, OrderItem, WishlistItem

from django.views.decorators.csrf import csrf_exempt


def home(request):
    products = Product.objects.filter(is_available=True)
    return render(request, 'store/home.html', {'products': products})




def add_to_cart(request, product_id):
    cart = request.session.get('cart', {})
    product_id = str(product_id)
    product = get_object_or_404(Product, pk=product_id)
    WishlistItem.objects.filter(user=request.user, product_id=product_id).delete()

    if product_id in cart:
        cart[product_id]['quantity'] += 1
    else:
        cart[product_id] = {
            'name': product.name,
            'price': float(product.price),  # ✅ convert Decimal to float
            'quantity': 1
        }

    request.session['cart'] = cart

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'message': 'Product added to cart',
            'cartCount': len(cart),
            'productName': product.name,
            'price': float(product.price),  # ✅ again
        })

    return redirect('view_cart')  # fallback



def view_cart(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total = 0
    for product_id, item in cart.items():
        product = get_object_or_404(Product, id=product_id)
        item_total = product.price * item['quantity']
        total += item_total
        cart_items.append({
            'product': product,
            'quantity': item['quantity'],
            'total': item_total
        })
    return render(request, 'store/cart.html', {'cart_items': cart_items, 'total': total})

def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})
    if str(product_id) in cart:
        del cart[str(product_id)]
    request.session['cart'] = cart
    return redirect('view_cart')




def update_cart(request, product_id, action):
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
    product = Product.objects.get(id=product_id)
    wishlist_item, created = WishlistItem.objects.get_or_create(user=request.user, product=product)
    if created:
        message = "Added to wishlist"
    else:
        message = "Already in wishlist"
    wishlist_count = WishlistItem.objects.filter(user=request.user).count()
    return JsonResponse({'message': message, 'wishlistCount': wishlist_count, 'productName': product.name})

@login_required
def remove_from_wishlist(request, product_id):
    product = Product.objects.get(id=product_id)
    WishlistItem.objects.filter(user=request.user, product=product).delete()
    wishlist_count = WishlistItem.objects.filter(user=request.user).count()
    return JsonResponse({'message': "Removed from wishlist", 'wishlistCount': wishlist_count, 'productName': product.name})

def wishlist_view(request):
    if not request.user.is_authenticated:
        messages.info(request, "Please log in to view your wishlist.")
        return redirect('login')  # make sure your login URL name is 'login'
    items = WishlistItem.objects.filter(user=request.user).select_related('product')
    return render(request, 'store/wishlist.html', {'wishlist_items': items})


def register(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()

    return render(request, 'store/register.html', {'form': form})

class UserRegisterView(CreateView):
    form_class = UserCreationForm
    template_name = 'store/register.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_staff = False
        user.is_superuser = False
        user.save()
        return super().form_valid(form)
    

@login_required
def checkout(request):
    cart = request.session.get('cart', {})
    if not cart:
        return redirect('home')  # or show a message that cart is empty

    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        address = request.POST.get('address')
        phone = request.POST.get('phone')

        total_price = 0
        for product_id, item in cart.items():
            total_price += Decimal(item['price']) * item['quantity']

        order = Order.objects.create(
            user=request.user,
            total_price=total_price,
            full_name=full_name,
            address=address,
            phone=phone,
        )

        for product_id, item in cart.items():
            product = Product.objects.get(pk=product_id)
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=item['quantity'],
                price=Decimal(item['price']),
            )

        # Clear cart
        request.session['cart'] = {}
        return render(request, 'store/order_success.html', {'order': order})

    return render(request, 'store/checkout.html')


def checkout_view(request):
    # Calculate total, create order, etc.
    total = 1000  # example amount
    order_id = 'ORDER1234'  # generate this dynamically
    total_in_paisa = int(total * 100)  # Khalti expects amount in paisa (smallest unit)
    context = {
        'total': total,
        'total_in_paisa': total_in_paisa,
        'order_id': order_id,
        # other context vars
    }
    return render(request, 'checkout.html', context)

    


@csrf_exempt
def verify_khalti_payment(request):
    import json
    if request.method == 'POST':
        data = json.loads(request.body)
        token = data.get('token')
        amount = data.get('amount')

        # Call Khalti API to verify payment
        payload = {
            "token": token,
            "amount": amount
        }
        headers = {
            "Authorization": "Key test_secret_key_abc123"  # Replace with your secret key
        }
        url = "https://khalti.com/api/v2/payment/verify/"
        response = requests.post(url, payload, headers=headers)
        if response.status_code == 200:
            return JsonResponse({"success": True})
        else:
            return JsonResponse({"success": False})
    return JsonResponse({"success": False})