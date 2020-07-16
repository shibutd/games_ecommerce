from decimal import Decimal
from django.test import TestCase
from .. import models, factories


class TestModel(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = factories.UserFactory.create()

    def setUp(self):
        self.products = factories.ProductFactory.create_batch(2)
        self.cart = models.Cart.objects.create(user=self.user)

    def test_in_stock_manager_works(self):
        p1, p2 = self.products
        p1.in_stock = True
        p1.save()
        p2.in_stock = True
        p2.save()

        factories.ProductFactory.create(in_stock=False)
        self.assertEqual(
            models.Product.objects.all().count(), 3)
        self.assertEqual(
            models.Product.objects.in_stock().count(), 2)

    def test_address_save_default_works(self):
        factories.AddressFactory.create(
            user=self.user,
            address_type=models.Address.SHIPPING,
            is_default=True
        )
        factories.AddressFactory.create(
            user=self.user,
            address_type=models.Address.BILLING,
            is_default=True
        )
        self.assertEqual(models.Address.objects.filter(
            user=self.user, is_default=True).count(), 2)

        new_shipping_address = factories.AddressFactory.build(
            user=self.user,
            address_type=models.Address.SHIPPING,
            is_default=True
        )
        new_shipping_address.save()

        self.assertEqual(models.Address.objects.filter(
            user=self.user).count(), 3)
        self.assertEqual(models.Address.objects.filter(
            user=self.user, is_default=True).count(), 2)

    def test_cart_is_empty_works(self):
        p1 = self.products[0]

        self.assertTrue(self.cart.is_empty())

        cartline = models.CartLine.objects.create(
            cart=self.cart, product=p1)

        self.assertFalse(self.cart.is_empty())

        cartline.delete()

        self.assertTrue(self.cart.is_empty())

    def test_cart_count_works(self):
        p1, p2 = self.products

        models.CartLine.objects.create(
            cart=self.cart, product=p1, quantity=2)

        self.assertEqual(self.cart.count(), 2)

        models.CartLine.objects.create(
            cart=self.cart, product=p2, quantity=1)

        self.assertEqual(self.cart.count(), 3)

    def test_cart_get_total_works(self):
        p1, p2 = self.products
        p1.price = Decimal(12.99)
        p1.save()
        p2.price = Decimal(15.99)
        p2.save()

        self.assertEqual(self.cart.get_total(), 0)

        models.CartLine.objects.create(
            cart=self.cart, product=p1, quantity=2)

        self.assertAlmostEqual(self.cart.get_total(),
                               Decimal(25.98), 2)

        models.CartLine.objects.create(
            cart=self.cart, product=p2, quantity=2)

        self.assertAlmostEqual(self.cart.get_total(),
                               Decimal(57.96), 2)

    def test_cart_get_all_products_works(self):
        p1, p2 = self.products

        models.CartLine.objects.create(
            cart=self.cart, product=p1)

        self.assertCountEqual(
            self.cart.get_all_products(), [p1.name])

        models.CartLine.objects.create(
            cart=self.cart, product=p2, quantity=2)

        self.assertCountEqual(
            self.cart.get_all_products(), [p1.name, p2.name])

    def test_cart_create_order_works(self):
        p1, p2 = self.products

        shipping = factories.AddressFactory.create(
            user=self.user, address_type=models.Address.SHIPPING)
        billing = factories.AddressFactory.create(
            user=self.user, address_type=models.Address.BILLING)

        models.CartLine.objects.create(cart=self.cart, product=p1)
        models.CartLine.objects.create(cart=self.cart, product=p2)

        order = self.cart.create_order(shipping, billing)
        self.assertEqual(models.Order.objects.count(), 1)

        order.refresh_from_db()

        self.assertEqual(order.user, self.user)
        self.assertEqual(order.cart, self.cart)
        self.assertEqual(order.shipping_address, shipping)
        self.assertEqual(order.billing_address, billing)
        self.assertEqual(order.status, models.Order.NEW)

    def test_cart_submit_works(self):
        p1, p2 = self.products

        models.CartLine.objects.create(cart=self.cart, product=p1)
        models.CartLine.objects.create(cart=self.cart, product=p2)

        models.Order.objects.create(user=self.user, cart=self.cart)

        order = self.cart.submit()
        order.refresh_from_db()

        lines = order.lines.all()
        self.assertCountEqual(
            [lines[0].product, lines[1].product], [p1, p2])

        self.assertEqual(models.Cart.objects.filter(
            status=models.Cart.SUBMITTED).count(), 1)
        self.assertEqual(models.CartLine.objects.filter(
            cart=self.cart).count(), 0)

    def test_cartline_get_total_product_price_works(self):
        p1, p2 = self.products
        p1.price = Decimal(12.99)
        p1.save()
        p2.price = Decimal(12.99)
        p2.discount_price = Decimal(11.99)
        p2.save()

        cartline = models.CartLine.objects.create(
            cart=self.cart, product=p1, quantity=2)

        self.assertAlmostEqual(cartline.get_total_product_price(),
                               Decimal(25.98))

        cartline = models.CartLine.objects.create(
            cart=self.cart, product=p2, quantity=2)

        self.assertAlmostEqual(cartline.get_total_product_price(),
                               Decimal(23.98))
