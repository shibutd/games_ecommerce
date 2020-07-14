from . import models


def cart_middleware(get_response):

    def middleware(request):
        if 'cart_id' in request.session:
            cart_id = request.session['cart_id']

            cart = models.Cart.objects.get(id=cart_id)
            request.cart = cart
        else:
            request.cart = None

        response = get_response(request)
        return response

    return middleware
