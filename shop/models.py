from __future__ import annotations

from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True)

    class Meta:
        verbose_name_plural = "categorias"

    def __str__(self) -> str:  # pragma: no cover
        return self.name


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    unit = models.CharField(max_length=30, default="un")
    price_cents = models.PositiveIntegerField()
    stock_qty = models.IntegerField(default=99999)
    is_active = models.BooleanField(default=True)

    slug = models.SlugField(max_length=220, unique=True)

    class Meta:
        indexes = [
            models.Index(fields=["is_active"]),
            models.Index(fields=["category", "is_active"]),
        ]

    def __str__(self) -> str:  # pragma: no cover
        return self.name


class Cart(models.Model):
    session_key = models.CharField(max_length=64, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:  # pragma: no cover
        return f"Cart({self.session_key})"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = [("cart", "product")]
        indexes = [
            models.Index(fields=["cart", "product"]),
        ]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.product_id} x {self.quantity}"


class Order(models.Model):
    class Status(models.TextChoices):
        pending = "pending", "Pendente"
        confirmed = "confirmed", "Confirmado"
        cancelled = "cancelled", "Cancelado"

    order_number = models.CharField(max_length=32, unique=True)
    session_key = models.CharField(max_length=64, blank=True, default="")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.pending)
    created_at = models.DateTimeField(auto_now_add=True)

    # Dados do cliente para entrega
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=40)
    postcode = models.CharField(max_length=20, blank=True, default="")
    city = models.CharField(max_length=120, default="Paulistana")
    district = models.CharField(max_length=140, blank=True, default="")
    street = models.CharField(max_length=160)
    number = models.CharField(max_length=20)
    reference = models.CharField(max_length=220, blank=True, default="")
    notes = models.TextField(blank=True, default="")

    total_price_cents = models.PositiveIntegerField(default=0)

    class Meta:
        indexes = [
            models.Index(fields=["created_at"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self) -> str:  # pragma: no cover
        return self.order_number


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, null=True, blank=True)

    product_name = models.CharField(max_length=200)
    unit = models.CharField(max_length=30, default="un")
    unit_price_cents = models.PositiveIntegerField()
    quantity = models.PositiveIntegerField()
    subtotal_cents = models.PositiveIntegerField()

    def __str__(self) -> str:  # pragma: no cover
        return f"OrderItem({self.product_name})"
