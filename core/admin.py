from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.urls import reverse
from django.utils.html import format_html
from .models import (
    User, Vehicle, VehicleType, Brand, VehicleModel,
    Category, SubCategory, Product, ProductImage, BulkDiscountTier,
    Cart, CartItem, Order, OrderItem, Wishlist, Review,
    Coupon, DeliveryAddress, SellerInformation, GrievanceOfficer
)

# ----------------- Custom User -----------------
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ['username', 'email', 'is_technician', 'phone_number', 'date_joined']
    list_filter = ['is_technician']
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('is_technician', 'phone_number', 'accepted_privacy_policy')}),
    )

admin.site.register(User, CustomUserAdmin)

# ----------------- Vehicle -----------------
@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_model_name', 'get_brand', 'get_type', 'year', 'created_at')
    list_filter = ('model__brand', 'model__type', 'year')
    search_fields = ('user__username', 'model__name', 'model__brand__name')

    def get_model_name(self, obj):
        return obj.model.name
    get_model_name.short_description = 'Model'

    def get_brand(self, obj):
        return obj.model.brand.name
    get_brand.short_description = 'Brand'

    def get_type(self, obj):
        return obj.model.type.name
    get_type.short_description = 'Vehicle Type'

@admin.register(VehicleType)
class VehicleTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'type']
    list_filter = ['type']
    search_fields = ['name']

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']

@admin.register(VehicleModel)
class VehicleModelAdmin(admin.ModelAdmin):
    list_display = ['name', 'brand', 'type', 'created_at']
    list_filter = ['brand', 'type']
    search_fields = ['name', 'brand__name']

# ----------------- Category -----------------
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at','image']
    search_fields = ['name']

@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'description']
    list_filter = ['category']
    search_fields = ['name', 'category__name']

# ----------------- Product and Bulk Discount -----------------
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

class BulkDiscountInline(admin.TabularInline):
    model = BulkDiscountTier
    extra = 1

# @admin.register(Product)
# class ProductAdmin(admin.ModelAdmin):
#     list_display = ('title', 'stock', 'stock_status_display', 'is_out_of_stock_manual')
#     list_editable = ('is_out_of_stock_manual',)
#     list_filter = ('brand', 'category', 'is_out_of_stock_manual')
#     search_fields = ('title', 'part_number')
#     inlines = [ProductImageInline, BulkDiscountInline]

#     def stock_status_display(self, obj):
#         return "Out of Stock" if obj.is_out_of_stock() else "In Stock"
#     stock_status_display.short_description = "Stock Status"


from ckeditor.widgets import CKEditorWidget
# from django import forms
from django.db import models

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'stock', 'stock_status_display', 'is_out_of_stock_manual')
    list_editable = ('is_out_of_stock_manual',)
    list_filter = ('brand', 'category', 'is_out_of_stock_manual')
    search_fields = ('title', 'part_number')
    inlines = [ProductImageInline, BulkDiscountInline]

    formfield_overrides = {
        # Apply CKEditor to any RichTextField in Product
        models.TextField: {'widget': CKEditorWidget},
    }

    def stock_status_display(self, obj):
        return "Out of Stock" if obj.is_out_of_stock() else "In Stock"
    stock_status_display.short_description = "Stock Status"


# ----------------- Cart and Order -----------------
class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 1

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'created_at']
    inlines = [CartItemInline]

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1

# core/admin.py
from django.contrib import admin
from .models import HeroSlider

@admin.register(HeroSlider)
class HeroSliderAdmin(admin.ModelAdmin):
    list_display = ("title", "order", "active")
    list_editable = ("order", "active")
    ordering = ("order",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_link', 'user', 'delivery_address', 'total_amount', 'status', 'coupon', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['id', 'user__username', 'delivery_address__full_name', 'delivery_address__pincode']
    inlines = [OrderItemInline]
    change_form_template = 'admin/order_change_form.html'

    def order_link(self, obj):
        url = reverse('admin:%s_%s_change' % (obj._meta.app_label, obj._meta.model_name), args=[obj.id])
        return format_html('<a href="{}">Order #{}</a>', url, obj.id)
    order_link.short_description = 'Order'

    def delivery_address(self, obj):
        return obj.delivery_address.full_name + ", " + obj.delivery_address.city + ", " + obj.delivery_address.state
    delivery_address.short_description = 'Delivery Address'

# ----------------- Other Models -----------------
@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'created_at']
    list_filter = ['user']

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['comment']

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_percentage', 'valid_from', 'valid_until', 'active']
    list_filter = ['active', 'valid_from', 'valid_until']

@admin.register(DeliveryAddress)
class DeliveryAddressAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'pincode', 'city', 'state', 'verified']
    list_filter = ['state', 'verified']
    search_fields = ['full_name', 'pincode', 'city', 'district']

@admin.register(SellerInformation)
class SellerInformationAdmin(admin.ModelAdmin):
    list_display = ['user', 'name', 'gstin', 'pan']
    search_fields = ['name', 'user__username', 'gstin', 'pan']

@admin.register(GrievanceOfficer)
class GrievanceOfficerAdmin(admin.ModelAdmin):
    list_display = ['name', 'designation', 'redressal_timeline']
    search_fields = ['name', 'designation']


from django.contrib import admin
from .models import WebsiteLogo

@admin.register(WebsiteLogo)
class WebsiteLogoAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'uploaded_at')
    list_filter = ('is_active',)
    search_fields = ('name',)