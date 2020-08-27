from django import template
from django.db.models import Prefetch
from games import models


register = template.Library()


@register.filter
def cart_item_count(request):
    cart = request.cart
    if cart:
        return cart.count()
    return 0


@register.filter
def related_with_lines(cart_id):
    if not cart_id:
        return []
    cartline_qs = models.CartLine.objects.select_related('product')
    cart = models.Cart.objects.prefetch_related(
        Prefetch('lines', queryset=cartline_qs)).get(pk=cart_id)
    return cart
