from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator

class User(AbstractUser):
    is_technician = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=15, blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username

class VehicleType(models.Model):
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=[('Car', 'Car'), ('Bike', 'Bike'), ('Scooter', 'Scooter'), ('Cycle', 'Cycle')])

    def __str__(self):
        return f"{self.name} ({self.type})"

class Brand(models.Model):
    name = models.CharField(max_length=100)
    logo = models.ImageField(upload_to='brands/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Vehicle(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vehicles')
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)
    model = models.CharField(max_length=100)
    year = models.PositiveIntegerField()
    type = models.ForeignKey(VehicleType, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.brand} {self.model} ({self.user})"
    
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class SubCategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('category', 'name')
        verbose_name_plural = "Subcategories"

    def __str__(self):
        return f"{self.category.name} → {self.name}"


class Product(models.Model):
    title = models.CharField(max_length=200)  # formerly name
    part_number = models.CharField(max_length=100, unique=True, null=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)

    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)

    #CATEGORY_CHOICES = []


    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products'
    )

    subcategory = models.ForeignKey(
        SubCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products'
    )

    compatible_vehicle_types = models.ManyToManyField(VehicleType, null=True, blank=True)

    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)

    slug = models.SlugField(unique=True, null=True, blank=True)

    discount_percentage = models.FloatField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    # bulk_discount_10 = models.FloatField(
    #     default=2,
    #     validators=[MinValueValidator(0), MaxValueValidator(100)]
    # )
    # bulk_discount_100 = models.FloatField(
    #     default=5,
    #     validators=[MinValueValidator(0), MaxValueValidator(100)]
    # )
    is_out_of_stock_manual = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    def is_out_of_stock(self):
        return self.stock == 0 or self.is_out_of_stock_manual

    def stock_status(self):
        if self.is_out_of_stock():
            return "Out of Stock"
        return "In Stock"


from decimal import Decimal

class BulkDiscountTier(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='bulk_discounts')
    min_quantity = models.PositiveIntegerField()
    discount_percentage = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    class Meta:
        unique_together = ('product', 'min_quantity')
        ordering = ['-min_quantity']  # Ensure we evaluate higher quantities first

    def __str__(self):
        return f"{self.product.title}: {self.discount_percentage}% off from {self.min_quantity}+"

# models.py

class DeliveryAddress(models.Model):
    order = models.OneToOneField('Order', on_delete=models.CASCADE, related_name='delivery_address')
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=15)
    email = models.EmailField(blank=True, null=True)
    pincode = models.CharField(max_length=10)
    city = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    local_address = models.TextField()
    landmark = models.CharField(max_length=255, blank=True, null=True)
    verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.full_name} - {self.pincode}"


class Coupon(models.Model):
    code = models.CharField(max_length=20, unique=True)
    discount_percentage = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.code

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart ({self.user})"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product} x{self.quantity}"

   

    def get_total_price(self):
        price = self.product.price  # Decimal
        quantity = self.quantity

        # Determine applicable bulk discount
        bulk_discount = Decimal('0.0')
        for tier in self.product.bulk_discounts.all():
            if quantity >= tier.min_quantity:
                bulk_discount = Decimal(tier.discount_percentage)
                break

        # Apply discount
        discounted_price = price * (Decimal('1.0') - bulk_discount / Decimal('100'))
        return discounted_price * quantity



from django.db import models
from decimal import Decimal
from django.conf import settings

class Order(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    gst = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_charge = models.DecimalField(max_digits=10, decimal_places=2, default=50)  # Default ₹50
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    coupon = models.ForeignKey('Coupon', on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id} ({self.user})"

    def calculate_total(self):
        # Calculate subtotal from order items
        subtotal = sum(item.get_total_price() for item in self.items.all())

        # GST calculation (18% assumed)
        gst = subtotal * Decimal('0.18')

        # Delivery charge (keep as-is or use default)
        delivery = self.delivery_charge or Decimal('50.00')

        # Base total before coupon
        total = subtotal + gst + delivery

        # Apply coupon discount if available and active
        if self.coupon and self.coupon.active:
            total *= Decimal(1 - self.coupon.discount_percentage / 100)

        # Round and save
        self.subtotal = subtotal
        self.gst = gst
        self.total_amount = total.quantize(Decimal('0.01'))  # round to 2 decimal places
        self.save()
        return self.total_amount


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price at time of order

    def __str__(self):
        return f"{self.product} x{self.quantity} (Order {self.order.id})"
    def get_total_price(self):
        return self.price * self.quantity

class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product} (Wishlist of {self.user})"

class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review for {self.product} by {self.user}"
    
class name(models.Model):
    a =  models.DecimalField(max_digits=10, decimal_places=2)