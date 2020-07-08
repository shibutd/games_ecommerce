from . import models
import logging


logger = logging.getLogger(__name__)


def cart_middleware(get_response):

    def middleware(request):
        if 'cart_id' in request.session:
            cart_id = request.session['cart_id']

            logger.warning('==== Cart_id in session: %d ====', cart_id)

            cart = models.Cart.objects.get(id=cart_id)
            request.cart = cart
        else:
            logger.warning('==== Cart_id not in session ====')

            request.cart = None

        response = get_response(request)
        return response

    return middleware
