import logging
from io import BytesIO
from PIL import Image
from django.core.files.base import ContentFile
from django.db.models.signals import pre_save, post_save, pre_delete, m2m_changed
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.core.cache import cache
from . import models


THUMBNAIL_SIZE = (300, 300)

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=models.ProductImage)
def generate_thumbnail(sender, instance, **kwargs):
    """
    Generate thumbnail before saving ProductImage.
    """
    # logger.warning("Generating thumbnail for product %d",
    #                instance.product.pk)

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
    Check if User had a Cart, put into primary Cart items
    that was added into Cart while he was unauthenticated.
    """
    anonymous_cart_id = request.session.get('cart_id')

    if anonymous_cart_id:
        anonymous_cart = models.Cart.objects.get(pk=anonymous_cart_id)
        try:
            # Check if User already has a Cart
            loggedin_cart = models.Cart.objects.get(user=user)
            # If yes, put every product_line into his Cart
            loggedin_cart_products = loggedin_cart.get_all_products()

            for line in anonymous_cart.lines.select_related('product'):
                product_name = line.product.name
                # If product already in Cart increase quantity
                if product_name in loggedin_cart_products:
                    loggedin_cart_line = loggedin_cart.lines.get(
                        product__name=product_name)
                    loggedin_cart_line.quantity += line.quantity
                    loggedin_cart_line.save()
                # Otherwise put it to the Cart
                else:
                    line.cart = loggedin_cart
                    line.save()

            anonymous_cart.delete()
            request.cart = loggedin_cart
            request.session['cart_id'] = loggedin_cart.pk

            # logger.warning("Merged basket to id %d", loggedin_cart.pk)

        except models.Cart.DoesNotExist:
            anonymous_cart.user = user
            anonymous_cart.save()

            # logger.warning("Assigned user to basket id {}".format(
            # anonymous_cart.id))
    else:
        try:
            loggedin_cart = models.Cart.objects.get(user=user)

            request.cart = loggedin_cart
            request.session['cart_id'] = loggedin_cart.pk

        except models.Cart.DoesNotExist:
            pass


@receiver(pre_delete, sender=models.ProductTag)
def producttag_post_delete_cache_clear(sender, instance, **kwargs):
    """Clear cache containing all tags list before
    deleting a tag.
    """
    cache.delete(instance.slug)
    cache.delete('all_tags')


@receiver(post_save, sender=models.ProductTag)
def producttag_post_save_cache_clear(sender, instance, created, **kwargs):
    """Clear cache containing all tags list after
    creating new tag.
    """
    if created:
        cache.delete('all_tags')


@receiver(pre_delete, sender=models.Product)
def product_post_delete_cache_clear(sender, instance, **kwargs):
    """Clear cache containing all products' list and tags relating
    to product being deleted before deleting a product.
    """
    for tag in instance.tags.all():
        cache.delete(tag.slug)
    cache.delete('all_products')


@receiver(post_save, sender=models.Product)
def product_post_save_cache_clear(sender, instance, created, **kwargs):
    """Clear cache containing all products' list after
    creating new product.
    """
    if created:
        cache.delete('all_products')


@receiver(m2m_changed, sender=models.Product.tags.through)
def product_m2m_changed_cache_clear(sender, instance, **kwargs):
    """Clear cache of tags relating to product
    after adding new tags to it.
    """
    for tag in instance.tags.all():
        cache.delete(tag.slug)
