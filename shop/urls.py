from django.urls import path

from . import views

urlpatterns = [
    path("", views.catalog, name="catalog"),
    path("produto/<int:product_id>/", views.product_detail, name="product_detail"),
    path("carrinho/", views.cart_page, name="cart"),
    path("checkout/", views.checkout_page, name="checkout"),
    # htmx endpoints
    path("htmx/cart/add/", views.cart_add, name="cart_add"),
    path("htmx/cart/update/", views.cart_update, name="cart_update"),
    path("htmx/cart/remove/", views.cart_remove, name="cart_remove"),
    path("htmx/checkout/place/", views.checkout_place, name="checkout_place"),
]

