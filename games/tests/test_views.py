from django.test import TestCase
from django.urls import reverse, resolve
from django.contrib import auth
from .. import views, models, forms, factories
import logging


logger = logging.getLogger(__name__)


class TestViews(TestCase):

    def test_homepage_page_works(self):
        response = self.client.get(reverse('games:home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')
        self.assertContains(response, 'Home')

    def test_homepage_url_resolves_homepageview(self):
        view = resolve('/')
        self.assertEqual(
            view.func.__name__,
            views.HomePageView.as_view().__name__
        )

    def test_about_us_page_works(self):
        response = self.client.get(reverse('games:about-us'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'about_us.html')
        self.assertContains(response, 'About us')

    def test_contact_us_page_works(self):
        response = self.client.get(reverse('games:contact-us'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'contact_us.html')
        self.assertContains(response, 'Contact us')
        self.assertIsInstance(
            response.context["form"], forms.ContactUsForm)

    def test_contact_us_url_resolves_contactusview(self):
        view = resolve('/contact-us/')
        self.assertEqual(
            view.func.__name__,
            views.ContactUsView.as_view().__name__
        )

    def test_home_page_returns_active(self):
        factories.ProductFactory()
        factories.ProductFactory(active=False)

        response = self.client.get(reverse("games:home"))
        product_list = models.Product.objects.active().order_by("name")
        self.assertEqual(
            list(response.context["products"]),
            list(product_list),
        )

class AddToCartTest(TestCase):

    def setUp(self):
        self.user = factories.UserFactory.create()
        self.product1, self.product2 = factories.ProductFactory.create_batch(2)

    def test_add_to_cart_loggedin_works(self):
        self.client.force_login(self.user)

        for _ in range(2):
            self.client.get(self.product1.get_add_to_cart_url())

        self.assertTrue(
            models.Cart.objects.filter(user=self.user).exists())
        self.assertEquals(models.CartLine.objects.filter(
            cart__user=self.user).count(), 1)

        self.client.get(self.product2.get_add_to_cart_url())

        self.assertEquals(models.CartLine.objects.filter(
            cart__user=self.user).count(), 2)

    def test_carts_merges(self):
        # create cart of user1, add 2 cb
        cart = models.Cart.objects.create(user=self.user)
        models.CartLine.objects.create(
            cart=cart, product=self.product1, quantity=2)

        self.assertEquals(models.Cart.objects.count(), 1)

        # anonymous user with empty cart tries get to order-summary
        # response = self.client.get(
        #     reverse("games:order-summary"))
        # self.assertRedirects(response, reverse("games:home"))

        # anonymous user adds items to his Cart
        self.client.get(self.product2.get_add_to_cart_url())

        self.assertEquals(models.Cart.objects.count(), 2)
        self.assertEquals(models.Cart.objects.filter(
            user=self.user).count(), 1)
        self.assertEquals(models.Cart.objects.filter(
            user=None).count(), 1)

        # anonymous user with not empty cart tries get to order-summary
        # response = self.client.get(
        #     reverse("games:order-summary"))
        # self.assertTemplateUsed(response, 'order_summary.html')

        self.client.force_login(self.user)
        self.assertTrue(auth.get_user(self.client).is_authenticated)

        # cart of user and anonymous cart merged
        self.assertEquals(models.Cart.objects.count(), 1)

        self.client.get(self.product2.get_add_to_cart_url())

        self.assertEquals(models.Cart.objects.count(), 1)

    def test_identical_products_merges(self):
        cart = models.Cart.objects.create(user=self.user)
        models.CartLine.objects.create(
            cart=cart, product=self.product1, quantity=2)

        self.client.get(self.product1.get_add_to_cart_url())

        self.assertEquals(models.Cart.objects.count(), 2)

        self.client.force_login(self.user)
        self.assertTrue(auth.get_user(self.client).is_authenticated)

        self.assertEquals(models.Cart.objects.count(), 1)

        self.assertEquals(models.CartLine.objects.count(), 1)
        self.assertEquals(models.CartLine.objects.filter(
            cart=cart, product=self.product1)[0].quantity, 3)


class RemoveFromCartTest(TestCase):

    def setUp(self):
        self.user = factories.UserFactory.create()
        self.product = models.Product.objects.create(
            name='God Of War', price=7.00, slug='god-of-war')

    def test_remove_from_cart_works(self):
        cart = models.Cart.objects.create(user=self.user)
        models.CartLine.objects.create(
            cart=cart, product=self.product, quantity=2)

        self.assertEquals(models.CartLine.objects.filter(
            cart=cart).count(), 1)

        self.client.force_login(self.user)
        self.client.get(reverse('games:remove-from-cart',
                                kwargs={'slug': self.product.slug}))

        self.assertEquals(models.Cart.objects.count(), 1)
        self.assertEquals(models.CartLine.objects.filter(
            cart=cart).count(), 0)

    def test_remove_single_from_cart_works(self):
        cart = models.Cart.objects.create(user=self.user)
        cartline = models.CartLine.objects.create(
            cart=cart, product=self.product, quantity=2)

        self.client.force_login(self.user)
        self.assertTrue(auth.get_user(self.client).is_authenticated)

        response = self.client.get(reverse('games:remove-single-from-cart',
                                           kwargs={'slug': self.product.slug}))
        self.assertEqual(response.status_code, 302)

        self.assertEquals(models.CartLine.objects.filter(
            cart=cart).count(), 1)

        # self.assertEquals(cartline.quantity, 1)

        self.client.get(reverse('games:remove-single-from-cart',
                                kwargs={'slug': self.product.slug}))

        self.assertEquals(models.CartLine.objects.filter(
            cart=cart).count(), 1)
        # self.assertEquals(cartline.quantity, 1)

    def test_invalid_item_redirects_404(self):
        response = self.client.get('/remove_from_cart/unknown_item/')

        # response = self.client.get(reverse('games:remove-from-cart',
        #                                    kwargs={'slug': 'unknown_item'}))
        self.assertEqual(response.status_code, 404)

    def test_remove_no_cart_redirects(self):
        response = self.client.get(reverse('games:remove-from-cart',
                                           kwargs={'slug': self.product.slug}))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('games:product',
                                               kwargs={'slug': self.product.slug}))

    def test_remove_item_not_in_cart_redirects(self):
        cart = models.Cart.objects.create(user=self.user)

        self.assertEquals(models.CartLine.objects.filter(
            cart=cart).count(), 0)

        self.client.force_login(self.user)
        response = self.client.get(reverse('games:remove-from-cart',
                                           kwargs={'slug': self.product.slug}))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('games:product',
                                               kwargs={'slug': self.product.slug}))


class CheckoutViewTest(TestCase):

    def setUp(self):
        self.user = factories.UserFactory.create()
        self.product = factories.ProductFactory.create()
        shipping_data = {
            'shipping-street_address': '1234 Main St',
            'shipping-apartment_address': '22',
            'shipping-zip_code': '25121251',
            'shipping-city': 'San Diego',
            'shipping-country': 'US',
            'shipping-is_default': False,
            'shipping-use_default': False,
        }
        billing_data = {
            'billing-street_address': '3124 Main St',
            'billing-apartment_address': '33',
            'billing-zip_code': '124124124',
            'billing-city': 'San Francisco',
            'billing-country': 'US',
            'billing-is_default': True,
            'billing-use_default': False,
        }
        self.form_data = {**shipping_data, **billing_data}

        self.use_default_form_data = {key: '' for key in self.form_data}
        self.use_default_form_data['shipping-is_default'] = False
        self.use_default_form_data['billing-is_default'] = False
        self.use_default_form_data['shipping-use_default'] = True
        self.use_default_form_data['billing-use_default'] = True

        self.client.force_login(self.user)
        self.client.get(self.product.get_add_to_cart_url())
        self.response = self.client.post(
            reverse('games:checkout'), self.form_data)

    def test_user_can_save_shipping_and_billing_addresses(self):
        self.assertEqual(self.response.status_code, 302)
        self.assertRedirects(self.response, reverse("games:payment"))

        self.assertEquals(len(models.Address.objects.filter(
            user=self.user)), 2)
        self.assertEquals(len(models.Address.objects.filter(
            user=self.user).filter(is_default=True)), 1)

    def test_if_user_can_have_only_one_unique_default_address_at_once(self):
        models.Address.objects.filter(user=self.user).update(is_default=True)
        self.assertEquals(models.Address.objects.filter(
            user=self.user).filter(is_default=True).count(), 2)

        self.client.get(self.product.get_add_to_cart_url())

        is_default_form_data = self.form_data.copy()
        is_default_form_data['shipping-is_default'] = True
        is_default_form_data['billing-is_default'] = True

        response = self.client.post(
            reverse('games:checkout'), is_default_form_data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("games:payment"))

        self.assertEquals(len(models.Address.objects.filter(
            user=self.user).filter(is_default=True)), 2)

    def test_user_can_use_default_address(self):
        models.Address.objects.filter(user=self.user).update(is_default=True)

        self.client.get(self.product.get_add_to_cart_url())
        response = self.client.post(
            reverse('games:checkout'), self.use_default_form_data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("games:payment"))

    def test_user_cant_use_not_existing_default_address(self):
        models.Address.objects.filter(
            user=self.user, address_type=models.Address.SHIPPING).delete()
        response = self.client.post(
            reverse('games:checkout'), self.use_default_form_data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("games:checkout"))


class PaymentViewTest(TestCase):

    def setUp(self):
        self.user = factories.UserFactory.create()

    def test_redirect_payment_view_works(self):
        # Redirect user if not authenticated
        response = self.client.get(reverse('games:payment'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response, '{}?next={}'.format(reverse("account_login"),
                                          reverse("games:payment"))
        )

        self.client.force_login(self.user)
        self.assertEquals(models.Cart.objects.filter(
            user=self.user, status=models.Cart.OPEN).count(), 0)

        # Redirect user if no open Cart
        response = self.client.get(reverse('games:payment'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("games:home"))

        models.Cart.objects.create(user=self.user)
        self.assertEquals(models.Cart.objects.filter(
            user=self.user, status=models.Cart.OPEN).count(), 1)

        self.assertEqual(models.Order.objects.filter(
            user=self.user, status=models.Order.NEW).count(), 0)

        # Redirect user if no new active Order
        response = self.client.get(reverse('games:payment'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("games:home"))

        models.Order.objects.create(user=self.user)
        self.assertEqual(len(models.Order.objects.filter(
            user=self.user, status=models.Order.NEW)), 1)

        response = self.client.get(reverse('games:payment'))
        self.assertEqual(response.status_code, 302)

        # User paid order
        response = self.client.post(reverse('games:payment'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("games:home"))

        # self.assertEqual(len(models.Order.objects.filter(
        #     user=self.user, status=models.Order.NEW)), 0)
        # self.assertEqual(len(models.Order.objects.filter(
        #     user=self.user, status=models.Order.PAID)), 1)

        # response = self.client.get(reverse('games:payment'))
        # self.assertEqual(response.status_code, 302)
        # self.assertRedirects(response, reverse("games:home"))

    # def test_products_page_filters_by_tags_and_active(self):
    #     factories.ProductFactory(active=True)
    #     factories.ProductFactory(active=False)

        # cb = models.Product.objects.create(
        #     name="The cathedral and the bazaar",
        #     slug="cathedral-bazaar",
        #     price=Decimal("10.00"),
        # )

        # cb.tags.create(name="Open source", slug="opensource")

        # models.Product.objects.create(
        #     name="Microsoft Windows guide",
        #     slug="microsoft-windows-guide",
        #     price=Decimal("12.00"),
        # )
        # response = self.client.get(
        #     reverse("products", kwargs={"tag": "opensource"})
        # )
        # self.assertEqual(response.status_code, 200)
        # self.assertContains(response, "BookTime")
        # product_list = (
        #     models.Product.objects.active()
        #     .filter(tags__slug="opensource")
        #     .order_by("name")
        # )
        # self.assertEqual(
        #     list(response.context["object_list"]),
        #     list(product_list),
        # )
