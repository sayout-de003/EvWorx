from rest_framework import serializers
from .models import User, Vehicle, VehicleType, Brand, Product, Cart, CartItem, Order, OrderItem, Wishlist, Review, Coupon

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone_number', 'is_technician', 'date_joined']

class VehicleTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleType
        fields = ['id', 'name', 'type']

class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['id', 'name', 'logo']

class VehicleSerializer(serializers.ModelSerializer):
    brand = BrandSerializer()
    type = VehicleTypeSerializer()
    class Meta:
        model = Vehicle
        fields = ['id', 'user', 'brand', 'model', 'year', 'type', 'created_at']

class ProductSerializer(serializers.ModelSerializer):
    compatible_vehicle_types = VehicleTypeSerializer(many=True)
    brand = BrandSerializer()
    class Meta:
        model = Product
        fields = ['id', 'title', 'description', 'image', 'brand', 'category', 'compatible_vehicle_types', 'price', 'discount_percentage', 'bulk_discount_10', 'bulk_discount_100', 'stock', 'created_at']

class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = ['id', 'code', 'discount_percentage', 'valid_from', 'valid_until', 'active']

class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer()
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'quantity', 'added_at', 'total_price']

    def get_total_price(self, obj):
        return obj.get_total_price()

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True)
    class Meta:
        model = Cart
        fields = ['id', 'user', 'items', 'created_at']

class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer()
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'quantity', 'price']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    coupon = CouponSerializer()
    class Meta:
        model = Order
        fields = ['id', 'user', 'total_amount', 'status', 'coupon', 'items', 'created_at']

class WishlistSerializer(serializers.ModelSerializer):
    product = ProductSerializer()
    class Meta:
        model = Wishlist
        fields = ['id', 'user', 'product', 'created_at']

class ReviewSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    product = ProductSerializer()
    class Meta:
        model = Review
        fields = ['id', 'user', 'product', 'rating', 'comment', 'created_at']