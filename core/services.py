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
        
        # Enforce MOQ
        if quantity < product.moq:
            quantity = product.moq

        if product.is_out_of_stock() or product.stock < quantity:
            return False, f"Insufficient stock. Available: {product.stock}"

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
        product = get_object_or_404(Product, id=product_id)
        
        if quantity < 1:
            CartService.remove_from_cart(request, product_id, cart)
            return True, "Item removed."

        # Enforce MOQ
        if quantity < product.moq:
            return False, f"Minimum order quantity for {product.title} is {product.moq}."

        if product.stock < quantity:
            return False, f"Insufficient stock. Available: {product.stock}"

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


def convert_query_to_order(query_id):
    from .models import Order, OrderItem, DeliveryAddress, WhatsAppQuery
    from django.db import transaction
    
    query = WhatsAppQuery.objects.get(id=query_id)

    with transaction.atomic():
        # 1. Create Order
        order = Order.objects.create(
            user=None,  # Inquiries are typically treated as guest orders until linked
            status='Pending',
            total_amount=query.total_amount
        )

        # 2. Copy customer info to DeliveryAddress
        DeliveryAddress.objects.create(
            order=order,
            full_name=query.customer_name,
            phone=query.phone,
            email=query.email,
            local_address=query.address,
            city=query.city,
            district=query.district or "",
            state=query.state or "",
            pincode=query.pincode,
            verified=True
        )

        # 3. Copy query items to OrderItems
        for item in query.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.price
            )
        
        # 4. Recalculate total (handles GST and other model logic)
        order.calculate_total(save=True)

        # 5. Mark query as accepted
        query.status = 'ACCEPT_AS_ORDER'
        query.save()

        return order
