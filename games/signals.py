import logging
from io import BytesIO
from PIL import Image
from django.core.files.base import ContentFile
from django.db.models.signals import pre_save
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from . import models


THUMBNAIL_SIZE = (300, 300)

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=models.ProductImage)
def generate_thumbnail(sender, instance, **kwargs):
    """
    Generate thumbnail before saving ProductImage.
    """
    logger.warning("Generating thumbnail for product %d",
                   instance.product.pk)

    image = Image.open(instance.image)
    image = image.convert("RGB")
    image.thumbnail(THUMBNAIL_SIZE, Image.ANTIALIAS)

    temp_thumb = BytesIO()
    image.save(temp_thumb, "JPEG")
    temp_thumb.seek(0)

    instance.thumbnail.save(
        instance.image.name,
        ContentFile(temp_thumb.read()),
        save=False,
    )
    temp_thumb.close()


@receiver(user_logged_in)
def merge_carts_if_found(sender, user, request, **kwargs):
    """
    Check if User had a Cart. Put into primary Cart items
    that was added into Cart while he was unauthenticated.
    """
    anonymous_cart_id = request.session.get('cart_id')

    # if anonymous_cart_id:
    #     logger.warning("Find anonymous cart with id")
    # else:
    #     logger.warning("Cant find cart")

    if anonymous_cart_id:
        anonymous_cart = models.Cart.objects.get(pk=anonymous_cart_id)
        try:
            # Check if User already has a Cart
            loggedin_cart = models.Cart.objects.get(
                user=user, status=models.Cart.OPEN)

            # If yes, put every product_line into his Cart
            loggedin_cart_products = loggedin_cart.get_all_products()

            for line in anonymous_cart.lines.select_related('product'):

                product_name = line.product.name

                if product_name in loggedin_cart_products:
                    loggedin_cart_line = loggedin_cart.lines.get(
                        product__name=product_name)
                    loggedin_cart_line.quantity += line.quantity
                    loggedin_cart_line.save()
                else:
                    line.cart = loggedin_cart
                    line.save()

            anonymous_cart.delete()
            request.cart = loggedin_cart
            request.session['cart_id'] = loggedin_cart.pk

            logger.warning("Merged basket to id %d", loggedin_cart.pk)

        except models.Cart.DoesNotExist:
            anonymous_cart.user = user
            anonymous_cart.save()

            logger.warning("Assigned user to basket id {}".format(
                anonymous_cart.id))
    else:
        try:
            loggedin_cart = models.Cart.objects.get(
                user=user, status=models.Cart.OPEN)

            request.cart = loggedin_cart
            request.session['cart_id'] = loggedin_cart.pk

        except models.Cart.DoesNotExist:
            pass
