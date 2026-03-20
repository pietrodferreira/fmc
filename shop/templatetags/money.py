from __future__ import annotations

from decimal import Decimal

from django import template

register = template.Library()


def _format_brl_from_cents(cents: int) -> str:
    value = Decimal(cents) / Decimal(100)
    # Formata 1.234,56 (pt-BR) sem dependências extras.
    s = f"{value:,.2f}"
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"


@register.filter(name="brl")
def brl_filter(value: int) -> str:
    try:
        cents = int(value)
    except (TypeError, ValueError):
        cents = 0
    return _format_brl_from_cents(cents)


@register.filter(name="mul")
def mul_filter(a: int, b: int) -> int:
    try:
        return int(a) * int(b)
    except (TypeError, ValueError):
        return 0

