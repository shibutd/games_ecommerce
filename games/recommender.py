import redis
from django.conf import settings
from . import models


r = redis.Redis(host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB)


class Recommender(object):

    def get_product_key(self, id):
        return 'product:{}:purchased_with'.format(id)

    def products_bought(self, products):
        product_ids = [p.id for p in products]
        for product_id in product_ids:
            for with_id in product_ids:
                # get the other products bought with each product
                if product_id != with_id:
                    # increment score for product purchased together
                    r.zincrby(
                        self.get_product_key(product_id), 1, with_id)

    def suggest_products(self, product, max_results=3):
        suggestions = r.zrange(
            self.get_product_key(product.id), 0, -1, desc=True)[:max_results]
        suggested_products_ids = [int(id) for id in suggestions]
        # get suggested products and sort by order of appearance
        suggested_products = list(models.Product.objects.filter(
            id__in=suggested_products_ids))
        suggested_products.sort(
            key=lambda x: suggested_products_ids.index(x.id))
        return suggested_products
