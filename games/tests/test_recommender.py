import redis
from django.test import TestCase
from django.conf import settings
from .. import factories
from ..recommender import Recommender


class TestRecommendationSystem(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.r = redis.Redis(host=settings.REDIS_HOST,
                            port=settings.REDIS_PORT,
                            db=settings.REDIS_DB)
        cls.recommender = Recommender()
        cls.products = factories.ProductFactory.create_batch(4)

    def setUp(self):
        self.r.flushdb()

    def test_get_product_key(self):
        product1 = self.products[0]
        key = self.recommender.get_product_key(product1.id)
        self.assertTrue(
            key, 'product:{}:purchased_with'.format(product1.id))

    def test_products_bought(self):
        product1, product2, product3, product4 = self.products

        # Buy together 1, 2, 3
        self.recommender.products_bought(
            [product1, product2, product3])

        key_1 = self.recommender.get_product_key(product1.id)
        key_2 = self.recommender.get_product_key(product2.id)
        key_3 = self.recommender.get_product_key(product3.id)

        self.assertCountEqual(self.r.zrange(key_1, 0, -1, withscores=True),
                              [(str(product2.id).encode(), 1.0),
                               (str(product3.id).encode(), 1.0)])
        self.assertCountEqual(self.r.zrange(key_2, 0, -1, withscores=True),
                              [(str(product3.id).encode(), 1.0),
                               (str(product1.id).encode(), 1.0)])
        self.assertCountEqual(self.r.zrange(key_3, 0, -1, withscores=True),
                              [(str(product1.id).encode(), 1.0),
                               (str(product2.id).encode(), 1.0)])

        # Buy together 1, 2, 4
        self.recommender.products_bought(
            [product1, product2, product4])

        self.assertEqual(self.r.zrange(key_1, 0, -1,
                                       desc=True, withscores=True)[0],
                         (str(product2.id).encode(), 2.0))
        self.assertEqual(self.r.zrange(key_2, 0, -1,
                                       desc=True, withscores=True)[0],
                         (str(product1.id).encode(), 2.0))
        self.assertCountEqual(self.r.zrange(key_3, 0, -1, withscores=True),
                              [(str(product1.id).encode(), 1.0),
                               (str(product2.id).encode(), 1.0)])

    def test_suggest_products(self):
        product1, product2, product3, product4 = self.products

        key_1 = self.recommender.get_product_key(product1.id)
        key_2 = self.recommender.get_product_key(product2.id)
        key_3 = self.recommender.get_product_key(product3.id)

        # Buy together 1, 2, 3
        for id in (product2.id, product3.id):
            self.r.zincrby(key_1, 1, id)
        for id in (product1.id, product3.id):
            self.r.zincrby(key_2, 1, id)
        for id in (product1.id, product2.id):
            self.r.zincrby(key_3, 1, id)

        # Buy together 1, 2
        self.r.zincrby(key_1, 1, product2.id)
        self.r.zincrby(key_2, 1, product1.id)

        self.assertEqual(self.recommender.suggest_products(product1),
                         [product2, product3])
        self.assertEqual(self.recommender.suggest_products(
            product1, max_results=1), [product2])
        self.assertEqual(self.recommender.suggest_products(product2),
                         [product1, product3])
        self.assertCountEqual(self.recommender.suggest_products(product3),
                              [product2, product1])
        self.assertEqual(self.recommender.suggest_products(product4),
                         [])
