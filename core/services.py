from django.shortcuts import get_object_or_404
from .models import Product, Cart, CartItem, Order, OrderItem
from decimal import Decimal

class CartService:
    @staticmethod
    def get_cart(request):
        if request.user.is_authenticated:
            cart, _ = Cart.objects.get_or_create(user=request.user)
            return cart
        return request.session.get('cart', {})

    @staticmethod
    def add_to_cart(request, product_id, quantity, cart=None):
        product = get_object_or_404(Product, id=product_id)
        if product.is_out_of_stock() or product.stock < quantity:
            return False, "Insufficient stock."

        if request.user.is_authenticated:
            if not cart:
                cart, _ = Cart.objects.get_or_create(user=request.user)
            cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
            if not created:
                cart_item.quantity += quantity
            else:
                cart_item.quantity = quantity
            cart_item.save()
        else:
            session_cart = request.session.get('cart', {})
            session_cart[str(product_id)] = session_cart.get(str(product_id), 0) + quantity
            request.session['cart'] = session_cart
            request.session.modified = True
        
        return True, "Item added to cart."

    @staticmethod
    def remove_from_cart(request, product_id, cart=None):
        if request.user.is_authenticated:
            if not cart:
                cart = Cart.objects.filter(user=request.user).first()
            if cart:
                CartItem.objects.filter(cart=cart, product_id=product_id).delete()
        else:
            session_cart = request.session.get('cart', {})
            session_cart.pop(str(product_id), None)
            request.session['cart'] = session_cart
            request.session.modified = True

    @staticmethod
    def update_cart_quantity(request, product_id, quantity, cart=None):
        if quantity < 1:
            CartService.remove_from_cart(request, product_id, cart)
            return True, "Item removed."

        if request.user.is_authenticated:
            if not cart:
                cart = Cart.objects.filter(user=request.user).first()
            if cart:
                cart_item = CartItem.objects.filter(cart=cart, product_id=product_id).first()
                if cart_item:
                    cart_item.quantity = quantity
                    cart_item.save()
        else:
            session_cart = request.session.get('cart', {})
            session_cart[str(product_id)] = quantity
            request.session['cart'] = session_cart
            request.session.modified = True
        
        return True, "Cart updated."

    @staticmethod
    def get_cart_items_and_total(request):
        cart_items = []
        total_price = Decimal('0.00')

        if request.user.is_authenticated:
            cart, _ = Cart.objects.get_or_create(user=request.user)
            items = cart.items.select_related('product__brand', 'product__category').all()
            total_price = sum(item.get_total_price() for item in items)
            cart_items = items
        else:
            session_cart = request.session.get('cart', {})
            for pid, qty in session_cart.items():
                try:
                    product = Product.objects.get(id=int(pid))
                    subtotal = product.price * qty
                    total_price += subtotal
                    cart_items.append({
                        'product': product,
                        'quantity': qty,
                        'subtotal': subtotal
                    })
                except (Product.DoesNotExist, ValueError):
                    continue
        
        return cart_items, total_price
