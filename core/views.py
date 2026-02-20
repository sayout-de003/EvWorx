from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.utils import timezone
from decimal import Decimal
import random

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import (
    User, Vehicle, VehicleType, Brand, Product, Cart, CartItem, 
    Order, OrderItem, Wishlist, Review, Coupon, Category, 
    HeroSlider, BlogPost, DeliveryAddress, WebsiteLogo
)
from .serializers import (
    UserSerializer, VehicleSerializer, VehicleTypeSerializer, 
    BrandSerializer, ProductSerializer, CartSerializer, 
    CartItemSerializer, OrderSerializer, OrderItemSerializer, 
    WishlistSerializer, ReviewSerializer, CouponSerializer
)
from .forms import SignupForm, LoginForm, VehicleForm, CartAddForm
from .services import CartService

def homepage(request):
    products = Product.objects.filter(stock__gt=0).select_related('brand', 'category').order_by('-id')[:6]
    categories = Category.objects.all()
    sliders = HeroSlider.objects.filter(active=True)
    return render(request, 'core/homepage.html', {
        'sliders': sliders,
        'products': products,
        'categories': categories,
    })

def about(request):
    return render(request, 'core/about.html')

def faq(request):
    return render(request, 'core/faq.html')

def blog(request):
    articles = BlogPost.objects.all()
    return render(request, 'core/blog.html', {'articles': articles})

def blog_detail(request, pk):
    article = get_object_or_404(BlogPost, pk=pk)
    return render(request, 'core/blog_detail.html', {'article': article})

def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created successfully!")
            return redirect('homepage')
        else:
            messages.error(request, "Registration failed. Please correct the errors.")
    else:
        form = SignupForm()
    return render(request, 'core/signup.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('homepage')
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = LoginForm()
    return render(request, 'core/login.html', {'form': form})

def user_logout(request):
    logout(request)
    return redirect('homepage')

@login_required
def garage(request):
    vehicles = Vehicle.objects.filter(user=request.user).select_related('brand', 'model', 'type')
    if request.method == 'POST':
        form = VehicleForm(request.POST)
        if form.is_valid():
            vehicle = form.save(commit=False)
            vehicle.user = request.user
            vehicle.save()
            messages.success(request, "Vehicle added to your garage!")
            return redirect('garage')
    else:
        form = VehicleForm()
    
    brands = Brand.objects.all()
    vehicle_types = VehicleType.objects.all()
    return render(request, 'core/garage.html', {
        'vehicles': vehicles, 
        'brands': brands, 
        'vehicle_types': vehicle_types,
        'form': form
    })

@login_required
def wishlist_view(request):
    wishlist = Wishlist.objects.filter(user=request.user).select_related('product__brand', 'product__category')
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        product = get_object_or_404(Product, id=product_id)
        Wishlist.objects.get_or_create(user=request.user, product=product)
        messages.success(request, f"{product.title} added to wishlist.")
        return redirect('wishlist')
    return render(request, 'core/wishlist.html', {'wishlist': wishlist})


def cart_view(request):
    cart_items, total_price = CartService.get_cart_items_and_total(request)
    
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        action = request.POST.get('action') # 'add', 'update', 'delete'
        
        if action == 'delete':
            CartService.remove_from_cart(request, product_id)
            messages.success(request, "Item removed from cart.")
        elif action == 'update':
            quantity = int(request.POST.get('quantity', 1))
            CartService.update_cart_quantity(request, product_id, quantity)
            messages.success(request, "Cart updated.")
        else: # Default is add
            form = CartAddForm(request.POST)
            if form.is_valid():
                quantity = form.cleaned_data['quantity']
                success, msg = CartService.add_to_cart(request, product_id, quantity)
                if success:
                    messages.success(request, msg)
                else:
                    messages.error(request, msg)
            else:
                messages.error(request, "Invalid quantity provided.")
        
        next_url = request.POST.get('next', 'cart')
        return redirect(next_url)

    return render(request, 'core/cart.html', {
        'cart_items': cart_items,
        'total_price': total_price,
    })


def wishlist_view(request):
    try:
        active_logo = WebsiteLogo.objects.get(is_active=True)
    except WebsiteLogo.DoesNotExist:
        active_logo = None
    if request.user.is_authenticated:
        wishlist = Wishlist.objects.filter(user=request.user).select_related('product__brand', 'product__category')
        if request.method == 'POST':
            product_id = request.POST['product_id']
            product = Product.objects.get(id=product_id)
            Wishlist.objects.get_or_create(user=request.user, product=product)
            return redirect('wishlist')
        return render(request, 'core/wishlist.html', {'wishlist': wishlist, 'logo': active_logo})

    wishlist_ids = request.session.get('wishlist', [])

    if request.method == 'POST':
        product_id = request.POST['product_id']
        if product_id not in wishlist_ids:
            wishlist_ids.append(product_id)
            request.session['wishlist'] = wishlist_ids
        return redirect('wishlist')

    wishlist_products = Product.objects.filter(id__in=wishlist_ids).select_related('brand', 'category')
    return render(request, 'core/wishlist.html', {'wishlist': wishlist_products, 'logo': active_logo})

@cache_page(60 * 15)
def catalog(request):
    products = Product.objects.select_related('brand', 'category').prefetch_related('compatible_vehicle_types', 'compatible_vehicle_models').all().order_by('-id')

    vehicle_id = request.GET.get('vehicle_id')
    category_id = request.GET.get('category')
    brand_id = request.GET.get('brand')
    search_query = request.GET.get('search')
    sort_option = request.GET.get('sort')

    if vehicle_id:
        try:
            vehicle = Vehicle.objects.get(id=vehicle_id)
            products = products.filter(compatible_vehicle_types=vehicle.type)
        except Vehicle.DoesNotExist:
            pass

    if category_id:
        products = products.filter(category_id=category_id)

    if brand_id:
        products = products.filter(brand_id=brand_id)

    if search_query:
        products = products.filter(title__icontains=search_query)

    if sort_option == 'price_asc':
        products = products.order_by('price')
    elif sort_option == 'price_desc':
        products = products.order_by('-price')
    elif sort_option == 'name_asc':
        products = products.order_by('title')
        products = products.order_by('title')
    elif sort_option == 'name_desc':
        products = products.order_by('-title')

    # Add pagination
    paginator = Paginator(products, 20)  # 20 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    brands = Brand.objects.all()
    categories = Category.objects.all()
    vehicle_types = VehicleType.objects.all()
    vehicles = Vehicle.objects.filter(user=request.user) if request.user.is_authenticated else []

    return render(request, 'core/catalog.html', {
        'products': page_obj.object_list,
        'page_obj': page_obj,
        'brands': brands,
        'categories': categories,
        'vehicle_types': vehicle_types,
        'vehicles': vehicles,
        'selected_vehicle': vehicle_id,
        'selected_category': category_id,
        'selected_brand': brand_id,
        'search_query': search_query,
        'selected_sort': sort_option,
    })

def order_create(request):
    # Get cart items
    items = []
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            items = list(cart.items.all())  # CartItem objects
        except Cart.DoesNotExist:
            items = []
    else:
        session_cart = request.session.get('cart', {})
        for product_id, quantity in session_cart.items():
            try:
                product = Product.objects.get(id=product_id)
                items.append({'product': product, 'quantity': quantity})
            except Product.DoesNotExist:
                continue

    if not items:
        messages.error(request, "Cart is empty")
        return redirect("cart")

    # Calculate total price for display
    total_price = 0
    if request.user.is_authenticated:
        for item in items:
            total_price += item.get_total_price()
    else:
        for item in items:
            total_price += item['product'].price * item['quantity']

    # Handle form POST
    if request.method == 'POST':
        # Store address in session
        request.session['address_data'] = {
            'full_name': request.POST['full_name'],
            'phone': request.POST['phone'],
            'email': request.POST.get('email'),
            'pincode': request.POST['pincode'],
            'city': request.POST['city'],
            'district': request.POST['district'],
            'state': request.POST['state'],
            'local_address': request.POST['local_address'],
            'landmark': request.POST.get('landmark'),
        }

        # Validate and store coupon
        coupon_code = request.POST.get('coupon_code')
        if coupon_code:
            try:
                coupon = Coupon.objects.get(
                    code=coupon_code, active=True,
                    valid_from__lte=timezone.now(),
                    valid_until__gte=timezone.now()
                )
                request.session['applied_coupon'] = coupon.code
            except Coupon.DoesNotExist:
                messages.error(request, 'Invalid or expired coupon')
                return redirect('order_create')

        return redirect('order_confirm')

    return render(request, 'core/order_create.html', {
        'cart_items': items,
        'total_price': total_price,
    })



def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    return render(request, 'core/product_detail.html', {'product': product})

@login_required
def add_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        Review.objects.create(
            user=request.user,
            product=product,
            rating=rating,
            comment=comment
        )
        messages.success(request, 'Review submitted successfully!')
        return redirect('product_detail', slug=product.slug)
    return redirect('product_detail', slug=product.slug)
def order_confirm(request):
    # Load cart again
    items = []
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            items = list(cart.items.select_related('product__brand', 'product__category').all())
        except Cart.DoesNotExist:
            items = []
    else:
        session_cart = request.session.get('cart', {})
        for product_id, quantity in session_cart.items():
            try:
                product = Product.objects.get(id=product_id)
                items.append({'product': product, 'quantity': quantity})
            except Product.DoesNotExist:
                continue

    if not items:
        messages.error(request, "Cart is empty")
        return redirect("cart")

    # Address & coupon from session
    address_data = request.session.get('address_data')
    if not address_data:
        messages.error(request, "Address details are missing.")
        return redirect("order_create")

    coupon = None
    coupon_code = request.session.get('applied_coupon')
    if coupon_code:
        try:
            coupon = Coupon.objects.get(code=coupon_code, active=True)
        except Coupon.DoesNotExist:
            coupon = None

    # Calculate subtotal
    subtotal = Decimal(0)
    order_items = []

    for item in items:
        if request.user.is_authenticated:
            product = item.product
            quantity = item.quantity
            price = product.price
        else:
            product = item['product']
            quantity = item['quantity']
            price = product.price

        subtotal += price * quantity
        order_items.append((product, quantity, price))

    gst = subtotal * Decimal('0.18')
    delivery = Decimal('50.00')
    total = subtotal + gst + delivery

    discount = Decimal(0)
    if coupon:
        discount = total * Decimal(coupon.discount_percentage / 100)
        total -= discount

    # Create Order
    order = Order.objects.create(
        user=request.user if request.user.is_authenticated else None,
        status='Pending',
        coupon=coupon,
        subtotal=subtotal,
        gst=gst,
        delivery_charge=delivery,
        total_amount=total
    )

    # Create Order Items
    for product, quantity, price in order_items:
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=quantity,
            price=price
        )

    # Save Address
    DeliveryAddress.objects.create(
        order=order,
        full_name=address_data['full_name'],
        phone=address_data['phone'],
        email=address_data.get('email'),
        pincode=address_data['pincode'],
        city=address_data['city'],
        district=address_data['district'],
        state=address_data['state'],
        local_address=address_data['local_address'],
        landmark=address_data.get('landmark'),
        verified=False
    )

    # Prepare cart items for template display
    cart_items = []
    if request.user.is_authenticated:
        cart_items = list(cart.items.all())
    else:
        # Create a simple class for anonymous user cart items
        class CartItemLike:
            def __init__(self, product, quantity):
                self.product = product
                self.quantity = quantity
            
            def get_total_price(self):
                return self.product.price * self.quantity
        
        # Convert session cart items to CartItem-like objects for template
        for item in items:
            cart_items.append(CartItemLike(item['product'], item['quantity']))

    # Clear cart
    if request.user.is_authenticated:
        cart.items.all().delete()
    else:
        request.session['cart'] = {}

    # Clear session data
    request.session.pop('address_data', None)
    request.session.pop('applied_coupon', None)

    return render(request, 'core/order_confirm.html', {
        'cart_items': cart_items,
        'order': order,
        'address': address_data,
        'total_breakdown': {
            'subtotal': subtotal,
            'gst': gst,
            'delivery': delivery,
            'discount': discount,
            'total': total
        },
    })

def order_payment(request):
    if request.user.is_authenticated:
        # Get the most recent order by the user
        order = Order.objects.filter(user=request.user).order_by('-created_at').first()
    else:
        # For guest checkout, pass order ID via GET/session
        order_id = request.GET.get('order_id')
        if not order_id:
            return render(request, 'core/order_payment.html', {'error': 'Order ID missing'})
        order = get_object_or_404(Order, id=order_id)

    if not order:
        return render(request, 'core/order_payment.html', {'error': 'Order not found'})

    return render(request, 'core/order_payment.html', {
        'order': order,
        'amount': order.total_amount,
        'payment_options': ['UPI', 'QR Code', 'Card', 'Cash on Delivery'],
    })


otp_store = {}

@csrf_exempt
def verify_phone(request):
    if request.method == 'POST':
        phone = request.POST.get('phone')
        otp = request.POST.get('otp')

        if otp:
            # Verify OTP
            saved_otp = otp_store.get(phone)
            if saved_otp and otp == saved_otp:
                del otp_store[phone]
                return JsonResponse({'status': 'verified'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Invalid OTP'})
        else:
            # Send OTP
            generated_otp = str(random.randint(100000, 999999))
            otp_store[phone] = generated_otp

            # TODO: Integrate actual SMS sending here
            print(f"OTP for {phone} is {generated_otp}")  # For testing

            return JsonResponse({'status': 'otp_sent'})

@staff_member_required
@csrf_protect
def admin_orders_view(request):
    orders = Order.objects.all().select_related('user', 'delivery_address').order_by('-created_at')

    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        new_status = request.POST.get('status')
        tracking_link = request.POST.get('tracking_link', '').strip()

        try:
            order = Order.objects.get(id=order_id)
            order.status = new_status
            order.tracking_link = tracking_link
            order.save()
            messages.success(request, f"Order #{order_id} updated.")
        except Order.DoesNotExist:
            messages.error(request, f"Order #{order_id} not found.")

        return redirect('admin_orders')

    return render(request, 'core/admin_orders.html', {'orders': orders})


# Existing ViewSets...
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class VehicleTypeViewSet(viewsets.ModelViewSet):
    queryset = VehicleType.objects.all()
    serializer_class = VehicleTypeSerializer
    permission_classes = [permissions.AllowAny]

class BrandViewSet(viewsets.ModelViewSet):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    permission_classes = [permissions.IsAdminUser]

class VehicleViewSet(viewsets.ModelViewSet):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Vehicle.objects.filter(user=self.request.user)

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = []  # Disable throttling for this public endpoint

    @action(detail=False, methods=['get'])
    def filter_by_vehicle(self, request):
        vehicle_id = request.query_params.get('vehicle_id')
        if vehicle_id:
            vehicle = Vehicle.objects.get(id=vehicle_id)
            products = Product.objects.filter(compatible_vehicle_types=vehicle.type)
            serializer = self.get_serializer(products, many=True)
            return Response(serializer.data)
        return Response({"error": "Vehicle ID required"}, status=status.HTTP_400_BAD_REQUEST)

class CartViewSet(viewsets.ModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)

    @action(detail=True, methods=['post'])
    def add_item(self, request, pk=None):
        cart = self.get_object()
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))
        product = Product.objects.get(id=product_id)
        if product.stock < quantity:
            return Response({"error": "Insufficient stock"}, status=status.HTTP_400_BAD_REQUEST)
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        if not created:
            cart_item.quantity += quantity
        else:
            cart_item.quantity = quantity
        cart_item.save()
        return Response(CartItemSerializer(cart_item).data)

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def create(self, request):
        cart = Cart.objects.get(user=request.user)
        if not cart.items.exists():
            return Response({"error": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)
        
        coupon_code = request.data.get('coupon_code')
        coupon = None
        if coupon_code:
            try:
                coupon = Coupon.objects.get(code=coupon_code, active=True, valid_from__lte=timezone.now(), valid_until__gte=timezone.now())
            except Coupon.DoesNotExist:
                return Response({"error": "Invalid or expired coupon"}, status=status.HTTP_400_BAD_REQUEST)
        
        order = Order.objects.create(user=request.user, status='Pending', coupon=coupon)
        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.get_total_price() / item.quantity
            )
        order.total_amount = order.calculate_total()
        order.save()
        cart.items.all().delete()
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

class WishlistViewSet(viewsets.ModelViewSet):
    queryset = Wishlist.objects.all()
    serializer_class = WishlistSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user)

class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Review.objects.filter(user=self.request.user)
    


from django.shortcuts import redirect
from core.models import Favicon  # replace with your model name
from django.conf import settings

def favicon_redirect(request):
    try:
        favicon_obj = Favicon.objects.first()  # get the uploaded favicon
        if favicon_obj and favicon_obj.icon:
            return redirect(favicon_obj.icon.url)
    except:
        pass
    # fallback
    return redirect(settings.STATIC_URL + 'core/favicon/favicon.svg')
