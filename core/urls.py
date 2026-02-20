from django.urls import path, include
from rest_framework.routers import DefaultRouter
from core.views import (
    UserViewSet, VehicleViewSet, VehicleTypeViewSet, BrandViewSet,  
    ProductViewSet, CartViewSet, OrderViewSet, WishlistViewSet, 
    ReviewViewSet, homepage, about, faq, blog, blog_detail, 
    signup, user_login, user_logout, catalog, garage, cart_view, 
    wishlist_view, order_create, order_confirm, order_payment, verify_phone, 
    product_detail, add_review, admin_orders_view, onsite_repair_booking,
    admin_management_hub, admin_repair_list, admin_repair_edit, 
    admin_order_list, admin_order_edit
)
from django.conf import settings
from django.conf.urls.static import static

# DRF Router for API endpoints
router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'vehicles', VehicleViewSet)
router.register(r'vehicle-types', VehicleTypeViewSet)
router.register(r'brands', BrandViewSet)
router.register(r'products', ProductViewSet)
router.register(r'carts', CartViewSet)
router.register(r'orders', OrderViewSet)
router.register(r'wishlist', WishlistViewSet)
router.register(r'reviews', ReviewViewSet)

urlpatterns = [
    # Public pages
    path('', homepage, name='homepage'),
    path('about/', about, name='about'),
    path('faq/', faq, name='faq'),
    path('blog/', blog, name='blog'),
    path('blog/<int:pk>/', blog_detail, name='blog_detail'),
    path('catalog/', catalog, name='catalog'),
    path('product/<slug:slug>/', product_detail, name='product_detail'),
    path('product/<int:product_id>/review/', add_review, name='add_review'),

    # Auth
    path('signup/', signup, name='signup'),
    path('login/', user_login, name='login'),
    path('logout/', user_logout, name='logout'),

    # Authenticated user pages
    path('garage/', garage, name='garage'),
    path('cart/', cart_view, name='cart'),
    path('wishlist/', wishlist_view, name='wishlist'),
    path('order/', order_create, name='order_create'),

    # path('order/', views.order_create, name='order_create'),
    path('order/confirm/', order_confirm, name='order_confirm'),
    path('order/payment/',order_payment, name='order_payment'),
    path('verify-phone/', verify_phone, name='verify_phone'),
    path('staff/orders/', admin_orders_view, name='admin_orders'), 


    path('onsite-repair-booking/', onsite_repair_booking, name='onsite_repair_booking'),

    # Admin Management
    path('admin-management/', admin_management_hub, name='admin_management_hub'),
    path('admin-management/repairs/', admin_repair_list, name='admin_repair_list'),
    path('admin-management/repairs/<int:pk>/edit/', admin_repair_edit, name='admin_repair_edit'),
    path('admin-management/orders/', admin_order_list, name='admin_order_list'),
    path('admin-management/orders/<int:pk>/edit/', admin_order_edit, name='admin_order_edit'),

    # API
    path('api/', include(router.urls)),
] #+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)