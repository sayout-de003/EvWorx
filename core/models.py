from decimal import Decimal
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models, transaction
from django.utils import timezone
from django.utils.text import slugify

# ----------------- Brand -----------------
class Brand(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    logo = models.ImageField(upload_to='brands/', blank=True, null=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


# ----------------- BulkDiscountTier -----------------
class BulkDiscountTier(models.Model):
    discount_percentage = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    min_quantity = models.PositiveIntegerField()
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='bulk_discounts')

    class Meta:
        ordering = ['-min_quantity']
        unique_together = ('product', 'min_quantity')
        verbose_name = "Bulk Discount Tier"
        verbose_name_plural = "Bulk Discount Tiers"

    def __str__(self):
        return f"{self.product.title}: {self.discount_percentage}% off from {self.min_quantity}+"


# ----------------- Cart -----------------
class Cart(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='carts')

    def __str__(self):
        return f"Cart ({self.user.username})"


# ----------------- CartItem -----------------
class CartItem(models.Model):
    added_at = models.DateTimeField(auto_now_add=True)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.product.title} x{self.quantity}"

    def get_total_price(self):
        price = self.product.price
        quantity = self.quantity
        bulk_discount = Decimal('0.0')
        for tier in self.product.bulk_discounts.all():
            if quantity >= tier.min_quantity:
                bulk_discount = Decimal(tier.discount_percentage)
                break
        discounted_price = price * (Decimal('1.0') - bulk_discount / Decimal('100'))
        return discounted_price * quantity


# ----------------- Category -----------------
class Category(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True)
    name = models.CharField(max_length=100, unique=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)

    class Meta:
        ordering = ['name']
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


# ----------------- Coupon -----------------
class Coupon(models.Model):
    active = models.BooleanField(default=True)
    code = models.CharField(max_length=20, unique=True)
    discount_percentage = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()

    def __str__(self):
        return self.code


# ----------------- DeliveryAddress -----------------
class DeliveryAddress(models.Model):
    city = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    full_name = models.CharField(max_length=255)
    landmark = models.CharField(max_length=255, blank=True, null=True)
    local_address = models.TextField()
    order = models.OneToOneField('Order', on_delete=models.CASCADE, related_name='delivery_address')
    phone = models.CharField(max_length=15)
    pincode = models.CharField(max_length=10)
    state = models.CharField(max_length=100)
    verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.full_name} - {self.pincode}"


# ----------------- GrievanceOfficer -----------------
class GrievanceOfficer(models.Model):
    contact_details = models.TextField()
    designation = models.CharField(max_length=100)
    name = models.CharField(max_length=255)
    redressal_timeline = models.CharField(max_length=255)

    def __str__(self):
        return self.name


# ----------------- HeroSlider -----------------
class HeroSlider(models.Model):
    title = models.CharField(max_length=200, help_text="Main heading for the slide")
    subtitle = models.CharField(max_length=300, blank=True, null=True, help_text="Optional subheading")
    button_text = models.CharField(max_length=100, blank=True, null=True)
    button_link = models.URLField(blank=True, null=True)
    background_color = models.CharField(max_length=50, default="bg-gradient-to-r from-blue-600 to-indigo-700")
    image = models.ImageField(upload_to="hero_slides/")
    order = models.PositiveIntegerField(default=0, help_text="Slide order (0 = first)")
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"Slide {self.order+1}: {self.title}"

    def clean(self):
        if not self.pk and HeroSlider.objects.count() >= 10:
            raise ValidationError("You can only have up to 10 slides.")

    def delete(self, *args, **kwargs):
        if HeroSlider.objects.count() <= 1:
            raise ValidationError("You must keep at least one slide.")
        super().delete(*args, **kwargs)


# ----------------- Manufacturer -----------------
class Manufacturer(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Manufacturer"
        verbose_name_plural = "Manufacturers"

    def __str__(self):
        return self.name


# ----------------- Order -----------------
class Order(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered')
    ]
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    created_at = models.DateTimeField(auto_now_add=True)
    delivery_charge = models.DecimalField(max_digits=10, decimal_places=2, default=50)
    gst = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tracking_link = models.URLField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey('User', on_delete=models.CASCADE, null=True, blank=True, related_name='orders')

    def __str__(self):
        if self.user:
            return f"Order {self.id} ({self.user.username})"
        elif hasattr(self, 'delivery_address'):
            return f"Order {self.id} ({self.delivery_address.full_name})"
        return f"Order {self.id} (Guest)"

    def calculate_total(self, save=True):
        subtotal = sum(item.get_total_price() for item in self.items.all())
        gst = subtotal * Decimal('0.18')
        delivery = self.delivery_charge or Decimal('50.00')
        total = subtotal + gst + delivery

        if self.coupon and self.coupon.active and (not self.coupon.valid_until or self.coupon.valid_until >= timezone.now()):
            total *= Decimal(1 - self.coupon.discount_percentage / 100)

        self.subtotal = subtotal
        self.gst = gst
        self.total_amount = total.quantize(Decimal('0.01'))

        if save:
            self.save()

        return self.total_amount

    def process_order(self):
        with transaction.atomic():
            for item in self.items.select_related('product'):
                product = item.product
                if product.stock < item.quantity:
                    raise ValidationError(f"Insufficient stock for '{product.title}' (Available: {product.stock}, Requested: {item.quantity})")
                product.stock -= item.quantity
                product.save()
            self.calculate_total(save=True)


# ----------------- OrderItem -----------------
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='order_items')
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.product.title} x{self.quantity} (Order {self.order.id})"

    def get_total_price(self):
        return self.price * self.quantity


# ----------------- Product -----------------
class Product(models.Model):
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='products')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    compatible_vehicle_models = models.ManyToManyField('VehicleModel', blank=True, related_name='products')
    compatible_vehicle_types = models.ManyToManyField('VehicleType', blank=True, related_name='products')
    country_of_origin = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True)
    discount_percentage = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    is_out_of_stock_manual = models.BooleanField(default=False)
    main_image = models.ImageField(upload_to='products/', blank=True, null=True)
    manufacturer = models.ForeignKey('Manufacturer', on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    mrp = models.DecimalField(max_digits=10, decimal_places=2)
    net_quantity = models.CharField(max_length=100, blank=True, null=True)
    part_number = models.CharField(max_length=100, unique=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    return_policy = models.TextField(blank=True, null=True)
    seller = models.ForeignKey('SellerInformation', on_delete=models.CASCADE, related_name='products', null=True, blank=True)
    slug = models.SlugField(unique=True, null=True, blank=True)
    stock = models.PositiveIntegerField(default=0)
    subcategory = models.ForeignKey('SubCategory', on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    title = models.CharField(max_length=200)
    updated_at = models.DateTimeField(auto_now=True)
    warranty_period = models.CharField(max_length=100, blank=True, null=True)
    warranty_terms = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def is_out_of_stock(self):
        return self.stock == 0 or self.is_out_of_stock_manual

    def stock_status(self):
        return "Out of Stock" if self.is_out_of_stock() else "In Stock"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)


# ----------------- ProductImage -----------------
class ProductImage(models.Model):
    alt_text = models.CharField(max_length=255, blank=True)
    image = models.ImageField(upload_to='product_images/')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')

    def __str__(self):
        return f"Image for {self.product.title}"


# ----------------- Review -----------------
class Review(models.Model):
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='reviews')

    def __str__(self):
        return f"Review for {self.product.title} by {self.user.username}"


# ----------------- SellerInformation -----------------
class SellerInformation(models.Model):
    address = models.TextField()
    commission_rate = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    gstin = models.CharField(max_length=15, blank=True, null=True)
    importer_details = models.TextField(blank=True, null=True)
    name = models.CharField(max_length=255)
    pan = models.CharField(max_length=10, blank=True, null=True)
    user = models.OneToOneField('User', on_delete=models.CASCADE, related_name='seller_info')

    def __str__(self):
        return self.name


# ----------------- SubCategory -----------------
class SubCategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories')
    created_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True)
    name = models.CharField(max_length=100)

    class Meta:
        ordering = ['name']
        unique_together = ('category', 'name')
        verbose_name = "Subcategory"
        verbose_name_plural = "Subcategories"

    def __str__(self):
        return f"{self.category.name} → {self.name}"


# ----------------- User -----------------
class User(AbstractUser):
    accepted_privacy_policy = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    is_technician = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=15, blank=True)

    def __str__(self):
        return self.username


# ----------------- Vehicle -----------------
class Vehicle(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    model = models.ForeignKey('VehicleModel', on_delete=models.CASCADE, related_name='vehicles')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vehicles')
    year = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.model.brand.name} {self.model.name} ({self.user.username})"


# ----------------- VehicleModel -----------------
class VehicleModel(models.Model):
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='vehicle_models')
    created_at = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=100)
    type = models.ForeignKey('VehicleType', on_delete=models.CASCADE, related_name='vehicle_models')

    class Meta:
        unique_together = ('name', 'brand', 'type')

    def __str__(self):
        return f"{self.brand.name} {self.name} ({self.type.name})"


# ----------------- VehicleType -----------------
class VehicleType(models.Model):
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=[
        ('Car', 'Car'),
        ('Bike', 'Bike'),
        ('Scooter', 'Scooter'),
        ('Cycle', 'Cycle'),
        ('E-Rikshaw', 'E-Rikshaw')
    ])

    def __str__(self):
        return f"{self.name} ({self.type})"


# ----------------- Wishlist -----------------
class Wishlist(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='wishlists')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlists')

    def __str__(self):
        return f"{self.product.title} (Wishlist of {self.user.username})"
