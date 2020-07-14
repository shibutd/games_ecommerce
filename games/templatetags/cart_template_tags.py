from django import template


register = template.Library()


@register.filter
def cart_item_count(request):
    cart = request.cart
    if cart:
        return cart.count()
    return 0
