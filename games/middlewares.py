from . import models
import logging


logger = logging.getLogger(__name__)


def cart_middleware(get_response):

    def middleware(request):
        # print(request)
        if 'cart_id' in request.session:
            cart_id = request.session['cart_id']
            # print(cart_id)
            logger.info('Cart_id in session:'.format({cart_id}))
            # try:
            cart = models.Cart.objects.get(id=cart_id)
            request.cart = cart
                
            # except models.Cart.DoesNotExist:
                # pass
        else:
            logger.info('Cart_id not in session')

            request.cart = None

        response = get_response(request)
        return response

    return middleware
