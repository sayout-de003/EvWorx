from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Vehicle, VehicleType, Brand, Product, Cart, CartItem, Order, OrderItem, Wishlist, Review, Coupon

# Custom User Admin
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ['username', 'email', 'is_technician', 'phone_number', 'date_joined']
    list_filter = ['is_technician']
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('is_technician', 'phone_number')}),
    )

# Inline for CartItem
class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 1

# Inline for OrderItem
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1

# Admin for Vehicle
@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ['user', 'brand', 'model', 'year', 'type', 'created_at']
    list_filter = ['brand', 'type', 'year']
    search_fields = ['model', 'user__username']

# Admin for VehicleType
@admin.register(VehicleType)
class VehicleTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'type']
    list_filter = ['type']
    search_fields = ['name']

# Admin for Brand
@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']


from .models import Category, SubCategory

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at']
    search_fields = ['name']

@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'description']
    list_filter = ['category']
    search_fields = ['name', 'category__name']


# Admin for Product
from django.contrib import admin
from .models import Product

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'stock', 'stock_status', 'is_out_of_stock_manual')
    list_editable = ('is_out_of_stock_manual',)
    list_filter = ('brand', 'category', 'is_out_of_stock_manual')
    search_fields = ('title', 'part_number')

    def stock_status(self, obj):
        return "Out of Stock" if obj.is_out_of_stock() else "In Stock"
    stock_status.short_description = "Stock Status"


# Admin for Cart
@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'created_at']
    inlines = [CartItemInline]

# Admin for Order
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'total_amount', 'status', 'coupon', 'created_at']
    list_filter = ['status', 'created_at']
    inlines = [OrderItemInline]

# Admin for Wishlist
@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'created_at']
    list_filter = ['user']

# Admin for Review
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['comment']

# Admin for Coupon
@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_percentage', 'valid_from', 'valid_until', 'active']
    list_filter = ['active', 'valid_from', 'valid_until']

# Register User with CustomUserAdmin
admin.site.register(User, CustomUserAdmin)




# admin.py
from django.contrib import admin
from .models import Product, BulkDiscountTier

class BulkDiscountInline(admin.TabularInline):
    model = BulkDiscountTier
    extra = 1

class ProductAdmin(admin.ModelAdmin):
    inlines = [BulkDiscountInline]


