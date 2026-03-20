from django.contrib import admin

from .models import Category, Cart, CartItem, Order, OrderItem, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name", "slug")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "unit", "price_cents", "stock_qty", "is_active")
    list_filter = ("is_active", "category")
    search_fields = ("name", "slug")


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("session_key", "is_active", "created_at", "updated_at")
    search_fields = ("session_key",)


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("cart", "product", "quantity")
    list_filter = ("cart", "product")
    search_fields = ("product__name",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("order_number", "status", "created_at", "full_name", "phone", "city")
    list_filter = ("status", "city")
    search_fields = ("order_number", "full_name", "phone")


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "product_name", "quantity", "unit_price_cents", "subtotal_cents")
    list_filter = ("order",)
    search_fields = ("product_name",)
