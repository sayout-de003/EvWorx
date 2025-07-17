from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import User, Vehicle, VehicleType, Brand, Product, Cart, CartItem, Order, OrderItem, Wishlist, Review, Coupon
from .serializers import UserSerializer, VehicleSerializer, VehicleTypeSerializer, BrandSerializer, ProductSerializer, CartSerializer, CartItemSerializer, OrderSerializer, OrderItemSerializer, WishlistSerializer, ReviewSerializer, CouponSerializer
from django.db.models import Q
from django.utils import timezone
from django.contrib import messages

def homepage(request):
    products = Product.objects.filter(stock__gt=0).order_by('-id')[:6] # Show 6 featured products
    return render(request, 'core/homepage.html', {'products': products})

def about(request):
    return render(request, 'core/about.html')

def faq(request):
    return render(request, 'core/faq.html')

def blog(request):
    # Mock blog articles (in a real app, you'd use a Blog model)
    articles = [
        {'id': 1, 'title': 'EV Battery Maintenance', 'content': 'Learn how to maintain your EV battery...'},
        {'id': 2, 'title': 'Choosing the Right Charger', 'content': 'Understand charger types...'},
    ]
    return render(request, 'core/blog.html', {'articles': articles})

def blog_detail(request, pk):
    # Mock blog detail
    articles = {
        1: {'title': 'EV Battery Maintenance', 'content': 'Detailed guide on maintaining EV batteries...'},
        2: {'title': 'Choosing the Right Charger', 'content': 'Comprehensive guide on charger types...'},
    }
    article = articles.get(pk, {})
    return render(request, 'core/blog_detail.html', {'article': article})

def signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        phone_number = request.POST.get('phone_number', '')
        is_technician = request.POST.get('is_technician', False) == 'on'
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
            return render(request, 'core/signup.html')
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            phone_number=phone_number,
            is_technician=is_technician
        )
        login(request, user)
        return redirect('homepage')
    return render(request, 'core/signup.html')

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('homepage')
        messages.error(request, 'Invalid credentials')
    return render(request, 'core/login.html')

def user_logout(request):
    logout(request)
    return redirect('homepage')

# @login_required
def garage(request):
    vehicles = Vehicle.objects.filter(user=request.user)
    if request.method == 'POST':
        brand_id = request.POST['brand']
        model = request.POST['model']
        year = request.POST['year']
        type_id = request.POST['type']
        Vehicle.objects.create(
            user=request.user,
            brand_id=brand_id,
            model=model,
            year=year,
            type_id=type_id
        )
        return redirect('garage')
    brands = Brand.objects.all()
    vehicle_types = VehicleType.objects.all()
    return render(request, 'core/garage.html', {'vehicles': vehicles, 'brands': brands, 'vehicle_types': vehicle_types})

# @login_required
from decimal import Decimal

# def cart_view(request):
#     if request.user.is_authenticated:
#         cart, _ = Cart.objects.get_or_create(user=request.user)
#         if request.method == 'POST':
#             product_id = request.POST['product_id']
#             quantity = int(request.POST.get('quantity', 1))
#             product = Product.objects.get(id=product_id)
#             if product.stock < quantity:
#                 messages.error(request, 'Insufficient stock')
#             else:
#                 cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
#                 cart_item.quantity = cart_item.quantity + quantity if not created else quantity
#                 cart_item.save()
#             return redirect('cart')
#         return render(request, 'core/cart.html', {'cart': cart})
    
#     # Anonymous session-based cart
#     cart = request.session.get('cart', {})

#     if request.method == 'POST':
#         product_id = request.POST['product_id']
#         quantity = int(request.POST.get('quantity', 1))
#         cart[product_id] = cart.get(product_id, 0) + quantity
#         request.session['cart'] = cart
#         messages.success(request, "Item added to cart")
#         return redirect('cart')

#     cart_items = []
#     total_price = Decimal('0.00')
#     for product_id, quantity in cart.items():
#         try:
#             product = Product.objects.get(id=product_id)
#             subtotal = product.price * quantity
#             total_price += subtotal
#             cart_items.append({'product': product, 'quantity': quantity, 'subtotal': subtotal})
#         except Product.DoesNotExist:
#             continue

#     return render(request, 'core/cart.html', {'cart_items': cart_items, 'total_price': total_price})


from decimal import Decimal
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Product, Cart, CartItem

def cart_view(request):
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)

        if request.method == 'POST':
            product_id = request.POST.get('product_id')
            if not product_id or not product_id.isdigit():
                messages.error(request, "Invalid product selected.")
                return redirect('cart')

            try:
                product = Product.objects.get(id=product_id)
            except Product.DoesNotExist:
                messages.error(request, "Product not found.")
                return redirect('cart')

            # DELETE ITEM
            if 'delete' in request.POST:
                CartItem.objects.filter(cart=cart, product=product).delete()
                messages.success(request, "Item removed from cart.")
                return redirect('cart')

            # UPDATE QUANTITY
            if 'update' in request.POST:
                quantity = int(request.POST.get('quantity', 1))
                cart_item = CartItem.objects.filter(cart=cart, product=product).first()
                if cart_item:
                    if quantity < 1:
                        cart_item.delete()
                        messages.success(request, "Item removed from cart.")
                    else:
                        cart_item.quantity = quantity
                        cart_item.save()
                        messages.success(request, "Cart updated.")
                return redirect('cart')

            # DEFAULT: ADD TO CART
            quantity = int(request.POST.get('quantity', 1))
            if product.is_out_of_stock() or product.stock < quantity:
                messages.error(request, 'This product is out of stock or does not have enough quantity.')
            else:
                cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
                if not created:
                    cart_item.quantity += quantity
                else:
                    cart_item.quantity = quantity
                cart_item.save()
                messages.success(request, "Item added to cart")
            return redirect('cart')

        # GET request
        cart_items = cart.items.all()
        total_price = sum(item.get_total_price() for item in cart_items)

        return render(request, 'core/cart.html', {
            'cart_items': cart_items,
            'total_price': total_price
        })

    else:
        # Anonymous user: session-based cart
        session_cart = request.session.get('cart', {})

        if request.method == 'POST':
            product_id = request.POST.get('product_id')
            if not product_id or not product_id.isdigit():
                messages.error(request, "Invalid product selected.")
                return redirect('cart')

            try:
                product = Product.objects.get(id=int(product_id))
            except Product.DoesNotExist:
                messages.error(request, "Product not found.")
                return redirect('cart')

            product_id_str = str(product.id)

            # DELETE
            if 'delete' in request.POST:
                if product_id_str in session_cart:
                    del session_cart[product_id_str]
                    request.session['cart'] = session_cart
                    request.session.modified = True
                    messages.success(request, "Item removed from cart.")
                return redirect('cart')

            # UPDATE
            if 'update' in request.POST:
                quantity = int(request.POST.get('quantity', 1))
                if quantity < 1 or not quantity.isdigit():
                    session_cart.pop(product_id_str, None)
                    messages.success(request, "Item removed from cart.")
                else:
                    session_cart[product_id_str] = quantity
                    messages.success(request, "Cart updated.")
                request.session['cart'] = session_cart
                request.session.modified = True
                return redirect('cart')

            # ADD
            quantity = int(request.POST.get('quantity', 1))
            if product.is_out_of_stock() or product.stock < quantity:
                messages.error(request, 'This product is out of stock or does not have enough quantity.')
            else:
                session_cart[product_id_str] = session_cart.get(product_id_str, 0) + quantity
                request.session['cart'] = session_cart
                request.session.modified = True
                messages.success(request, "Item added to cart")

            return redirect('cart')

        # GET: Display session cart
        cart_items = []
        total_price = Decimal('0.00')
        for product_id, quantity in session_cart.items():
            try:
                product = Product.objects.get(id=int(product_id))
                subtotal = product.price * quantity
                total_price += subtotal
                cart_items.append({
                    'product': product,
                    'quantity': quantity,
                    'subtotal': subtotal
                })
            except (Product.DoesNotExist, ValueError):
                continue

        return render(request, 'core/cart.html', {
            'cart_items': cart_items,
            'total_price': total_price
        })



# @login_required
def wishlist_view(request):
    if request.user.is_authenticated:
        wishlist = Wishlist.objects.filter(user=request.user)
        if request.method == 'POST':
            product_id = request.POST['product_id']
            product = Product.objects.get(id=product_id)
            Wishlist.objects.get_or_create(user=request.user, product=product)
            return redirect('wishlist')
        return render(request, 'core/wishlist.html', {'wishlist': wishlist})
    
    wishlist_ids = request.session.get('wishlist', [])

    if request.method == 'POST':
        product_id = request.POST['product_id']
        if product_id not in wishlist_ids:
            wishlist_ids.append(product_id)
            request.session['wishlist'] = wishlist_ids
        return redirect('wishlist')

    wishlist_products = Product.objects.filter(id__in=wishlist_ids)
    return render(request, 'core/wishlist.html', {'wishlist': wishlist_products})

# def catalog(request):
#     products = Product.objects.all().order_by('-id')
#     vehicle_id = request.GET.get('vehicle_id')
#     category = request.GET.get('category')
#     brand_id = request.GET.get('brand')
#     if vehicle_id:
#         vehicle = Vehicle.objects.get(id=vehicle_id)
#         products = products.filter(compatible_vehicle_types=vehicle.type)
#     if category:
#         products = products.filter(category=category)
#     if brand_id:
#         products = products.filter(brand_id=brand_id)
#     brands = Brand.objects.all()
#     vehicle_types = VehicleType.objects.all()
#     vehicles = Vehicle.objects.filter(user=request.user) if request.user.is_authenticated else []
#     return render(request, 'core/catalog.html', {
#         'products': products,
#         'brands': brands,
#         'vehicle_types': vehicle_types,
#         'vehicles': vehicles,
#         'selected_vehicle': vehicle_id,
#         'selected_category': category,
#         'selected_brand': brand_id
#     })

from django.shortcuts import render
from .models import Product, Brand, Vehicle, VehicleType, Category

def catalog(request):
    products = Product.objects.all().order_by('-id')

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
    elif sort_option == 'name_desc':
        products = products.order_by('-title')

    brands = Brand.objects.all()
    categories = Category.objects.all()
    vehicle_types = VehicleType.objects.all()
    vehicles = Vehicle.objects.filter(user=request.user) if request.user.is_authenticated else []

    return render(request, 'core/catalog.html', {
        'products': products,
        'brands': brands,
        'categories': categories,
        'vehicle_types': vehicle_types,
        'vehicles': vehicles,
        'selected_vehicle': vehicle_id,
        'selected_category': category_id,
        'selected_brand': brand_id,
        'search_query': search_query,
        'selected_sort': sort_option
    })


# @login_required
def order_create(request):
    if request.user.is_authenticated:
        cart = Cart.objects.get(user=request.user)
        items = cart.items.all()
    else:
        session_cart = request.session.get('cart', {})
        items = []
        for product_id, quantity in session_cart.items():
            try:
                product = Product.objects.get(id=product_id)
                items.append({'product': product, 'quantity': quantity})
            except Product.DoesNotExist:
                continue

    if not items:
        messages.error(request, 'Cart is empty')
        return redirect('cart')

    if request.method == 'POST':
        coupon = None
        coupon_code = request.POST.get('coupon_code')
        if coupon_code:
            try:
                coupon = Coupon.objects.get(code=coupon_code, active=True, valid_from__lte=timezone.now(), valid_until__gte=timezone.now())
            except Coupon.DoesNotExist:
                messages.error(request, 'Invalid or expired coupon')
                return redirect('order_create')

        # Create order (assign to user if logged in, else anonymous)
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            status='Pending',
            coupon=coupon
        )

        for item in items:
            OrderItem.objects.create(
                order=order,
                product=item['product'],
                quantity=item['quantity'],
                price=item['product'].price
            )

        order.total_amount = order.calculate_total()
        order.save()

        if request.user.is_authenticated:
            cart.items.all().delete()
        else:
            request.session['cart'] = {}

        messages.success(request, 'Order placed successfully')
        return redirect('homepage')

    return render(request, 'core/order_create.html', {'cart_items': items})


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