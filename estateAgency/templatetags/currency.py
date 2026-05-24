from decimal import Decimal, InvalidOperation
from django import template

register = template.Library()

@register.filter
def eur(value):
    try:
        value = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return value

    if value == value.to_integral():
        formatted = f"{value:,.0f}"
    else:
        formatted = f"{value:,.2f}"

    return (
        formatted
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )