from io import BytesIO
import logging
from PIL import Image
from django.conf import settings
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
    Signal to generate thumbnail before saving ProductImage.
    """
    logger.info(f"Generating thumbnail for product {instance.product.pk}")

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


@receiver(user_logged_in, sender=settings.AUTH_USER_MODEL)
def merge_carts_if_found(sender, user, request, **kwargs):
    """
    Signal to check if User has a primary Cart, then put
    items that he added into Cart while he was unauthenticated
    into his primary Cart.
    """
    anonymous_cart = getattr(request, "cart", None)
    if anonymous_cart:
        try:
            # Check if User already put products to his Cart
            # when he was logged in last time
            loggedin_cart = models.Cart.objects.get(
                user=user, status=models.Cart.OPEN)
            # If yes, put every product_line into his Cart
            for line in anonymous_cart.lines.all():
                line.cart = loggedin_cart
                line.save()

            anonymous_cart.delete()
            request.cart = loggedin_cart

            logger.info("Merged basket to id {}".format(
                loggedin_cart.id))

        except models.Cart.DoesNotExist:
            anonymous_cart.user = user
            anonymous_cart.save()

            logger.info("Assigned user to basket id {}".format(
                anonymous_cart.id))
