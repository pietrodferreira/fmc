from __future__ import annotations

import uuid
from typing import Any

from django.contrib import messages
from django.db import transaction
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from .models import Cart, CartItem, Category, Order, OrderItem, Product


def _ensure_session(request: HttpRequest) -> None:
    """
    Garante que `request.session.session_key` exista.
    O carrinho é persistido por sessão (anonimamente também).
    """
    if not request.session.session_key:
        request.session.save()


def _get_active_cart(request: HttpRequest, *, create: bool = True) -> Cart | None:
    _ensure_session(request)
    session_key = request.session.session_key
    if not session_key:
        return None

    cart = Cart.objects.filter(session_key=session_key, is_active=True).first()
    if cart is None and create:
        cart = Cart.objects.create(session_key=session_key, is_active=True)
    return cart


def _cart_items(cart: Cart | None) -> list[CartItem]:
    if not cart:
        return []
    return list(cart.items.select_related("product").all())


def _cart_summary_context(request: HttpRequest) -> dict[str, Any]:
    cart = _get_active_cart(request, create=False)
    items = _cart_items(cart)
    items_count = sum(i.quantity for i in items)
    total_price_cents = sum(i.quantity * i.product.price_cents for i in items)
    return {
        "cart_items_count": items_count,
        "cart_total_price_cents": total_price_cents,
    }


def _order_number() -> str:
    # Curto e legível para UI. Em caso de colisão, repetimos.
    return uuid.uuid4().hex[:10].upper()


@require_GET
def catalog(request: HttpRequest) -> HttpResponse:
    products = (
        Product.objects.filter(is_active=True)
        .select_related("category")
        .order_by("category__name", "name")
    )
    categories = Category.objects.all().order_by("name")

    context = {
        "products": products,
        "categories": categories,
        **_cart_summary_context(request),
    }
    return render(request, "shop/catalog.html", context)


@require_GET
def product_detail(request: HttpRequest, product_id: int) -> HttpResponse:
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    context = {
        "product": product,
        **_cart_summary_context(request),
    }
    return render(request, "shop/product_detail.html", context)


@require_GET
def cart_page(request: HttpRequest) -> HttpResponse:
    cart = _get_active_cart(request, create=True)
    assert cart is not None
    items = _cart_items(cart)
    total_price_cents = sum(i.quantity * i.product.price_cents for i in items)
    context = {
        "items": items,
        "cart": cart,
        "cart_total_price_cents": total_price_cents,
        **_cart_summary_context(request),
    }
    return render(request, "shop/cart.html", context)


@require_GET
def checkout_page(request: HttpRequest) -> HttpResponse:
    cart = _get_active_cart(request, create=False)
    items = _cart_items(cart) if cart else []
    if not items:
        messages.info(request, "Seu carrinho está vazio.")
        return redirect("cart")

    total_price_cents = sum(i.quantity * i.product.price_cents for i in items)
    context = {
        "items": items,
        "cart_total_price_cents": total_price_cents,
        **_cart_summary_context(request),
    }
    return render(request, "shop/checkout.html", context)


def _require_cart_or_400(request: HttpRequest) -> Cart | HttpResponseBadRequest:
    cart = _get_active_cart(request, create=False)
    if not cart:
        return HttpResponseBadRequest("Carrinho não encontrado.")
    return cart


@require_POST
def cart_add(request: HttpRequest) -> HttpResponse:
    product_id = request.POST.get("product_id")
    quantity_raw = request.POST.get("quantity")
    if not product_id:
        return HttpResponseBadRequest("`product_id` é obrigatório.")

    product = get_object_or_404(Product, pk=product_id, is_active=True)
    try:
        quantity = int(quantity_raw or "1")
    except ValueError:
        return HttpResponseBadRequest("`quantity` inválida.")

    if quantity <= 0:
        return HttpResponseBadRequest("`quantity` deve ser >= 1.")

    cart = _get_active_cart(request, create=True)
    assert cart is not None

    with transaction.atomic():
        item, _created = CartItem.objects.select_for_update().get_or_create(cart=cart, product=product)
        next_qty = item.quantity + quantity
        if product.stock_qty and product.stock_qty > 0:
            next_qty = min(next_qty, product.stock_qty)
        item.quantity = next_qty
        item.save()

    messages.success(request, f"Adicionado: {product.name} (x{quantity}).")
    return render(request, "shop/partials/cart_summary.html", _cart_summary_context(request))


@require_POST
def cart_update(request: HttpRequest) -> HttpResponse:
    cart = _require_cart_or_400(request)
    if isinstance(cart, HttpResponseBadRequest):
        return cart

    product_id = request.POST.get("product_id")
    quantity_raw = request.POST.get("quantity")
    if not product_id:
        return HttpResponseBadRequest("`product_id` é obrigatório.")

    product = get_object_or_404(Product, pk=product_id, is_active=True)
    try:
        quantity = int(quantity_raw or "0")
    except ValueError:
        return HttpResponseBadRequest("`quantity` inválida.")

    item = get_object_or_404(CartItem, cart=cart, product=product)

    with transaction.atomic():
        if quantity <= 0:
            item.delete()
        else:
            if product.stock_qty and product.stock_qty > 0:
                quantity = min(quantity, product.stock_qty)
            item.quantity = quantity
            item.save()

    messages.success(request, "Carrinho atualizado.")
    return render(
        request,
        "shop/partials/cart_items.html",
        {"items": _cart_items(cart), **_cart_summary_context(request)},
    )


@require_POST
def cart_remove(request: HttpRequest) -> HttpResponse:
    cart = _require_cart_or_400(request)
    if isinstance(cart, HttpResponseBadRequest):
        return cart

    product_id = request.POST.get("product_id")
    if not product_id:
        return HttpResponseBadRequest("`product_id` é obrigatório.")

    product = get_object_or_404(Product, pk=product_id)
    CartItem.objects.filter(cart=cart, product=product).delete()

    messages.info(request, "Item removido.")
    return render(
        request,
        "shop/partials/cart_items.html",
        {"items": _cart_items(cart), **_cart_summary_context(request)},
    )


def _validate_address(request: HttpRequest) -> dict[str, str] | None:
    required = ["full_name", "phone", "street", "number", "district", "city", "postcode"]
    data = {k: (request.POST.get(k) or "").strip() for k in required}
    missing = [k for k, v in data.items() if not v]
    if missing:
        return None

    return {
        **data,
        "reference": (request.POST.get("reference") or "").strip(),
        "notes": (request.POST.get("notes") or "").strip(),
    }


@require_POST
def checkout_place(request: HttpRequest) -> HttpResponse:
    cart = _get_active_cart(request, create=False)
    items = _cart_items(cart) if cart else []
    if not items:
        return HttpResponseBadRequest("Carrinho vazio.")

    addr = _validate_address(request)
    if not addr:
        messages.error(request, "Preencha corretamente os dados de entrega.")
        return render(
            request,
            "shop/partials/checkout_result.html",
            {"ok": False, **_cart_summary_context(request)},
        )

    total_price_cents = sum(i.quantity * i.product.price_cents for i in items)

    with transaction.atomic():
        order_number = _order_number()
        while Order.objects.filter(order_number=order_number).exists():
            order_number = _order_number()

        order = Order.objects.create(
            order_number=order_number,
            session_key=cart.session_key if cart else "",
            status=Order.Status.confirmed,
            full_name=addr["full_name"],
            phone=addr["phone"],
            postcode=addr["postcode"],
            city=addr["city"] or "Paulistana",
            district=addr["district"],
            street=addr["street"],
            number=addr["number"],
            reference=addr["reference"],
            notes=addr["notes"],
            total_price_cents=total_price_cents,
        )

        OrderItem.objects.bulk_create(
            [
                OrderItem(
                    order=order,
                    product=i.product,
                    product_name=i.product.name,
                    unit=i.product.unit,
                    unit_price_cents=i.product.price_cents,
                    quantity=i.quantity,
                    subtotal_cents=i.quantity * i.product.price_cents,
                )
                for i in items
            ]
        )

        # Fecha carrinho e limpa itens
        if cart:
            Cart.objects.filter(pk=cart.pk).update(is_active=False)
            cart.items.all().delete()

    messages.success(request, f"Pedido criado: {order.order_number}")
    return render(
        request,
        "shop/partials/checkout_result.html",
        {"ok": True, "order": order, "cart_total_price_cents": total_price_cents, **_cart_summary_context(request)},
    )
