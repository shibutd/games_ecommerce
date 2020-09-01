import logging
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse, resolve
from django.contrib import auth
from .. import views, models, forms, factories


logger = logging.getLogger(__name__)


class TestHomePage(TestCase):

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

    def test_home_page_filters_by_tags_and_in_stock(self):
        product1 = factories.ProductFactory.create(in_stock=True)
        product2 = factories.ProductFactory.create(in_stock=False)

        tag = models.ProductTag.objects.create(
            name="3D Action", slug="3d-action")

        product1.tags.add(tag)
        product2.tags.add(tag)

        response = self.client.get(reverse("games:home"))
        self.assertEqual(response.status_code, 200)

        in_stock_list = models.Product.objects.in_stock().order_by("name")
        self.assertEqual(
            list(response.context["object_list"]),
            list(in_stock_list),
        )

        response = self.client.get('{0}?tag={1}'.format(
            reverse("games:home"), '3d-action'))
        self.assertEqual(response.status_code, 200)

        in_stock_tagged_list = (
            models.Product.objects.in_stock()
            .filter(tags__slug="3d-action")
            .order_by("name")
        )
        self.assertEqual(
            list(response.context["object_list"]),
            list(in_stock_tagged_list),
        )


class TestAboutUsPage(TestCase):

    def test_about_us_page_works(self):
        response = self.client.get(reverse('games:about-us'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'about_us.html')
        self.assertContains(response, 'About us')


class TestContactUsPage(TestCase):

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


class TestAddToCart(TestCase):

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

    def test_anonymous_cart_becomes_main(self):
        # user is not authenticated
        self.assertFalse(auth.get_user(self.client).is_authenticated)

        # user adds products to cart
        self.client.get(self.product1.get_add_to_cart_url())
        self.client.get(self.product2.get_add_to_cart_url())

        # there is only one cart that is anonymous
        self.assertEquals(models.Cart.objects.count(), 1)
        self.assertFalse(models.Cart.objects.filter(
            user=self.user).exists())
        anonymous_cart = models.Cart.objects.all().first()
        anonymous_cart_id = anonymous_cart.id

        # user logged in
        self.client.force_login(self.user)
        self.assertEquals(models.Cart.objects.count(), 1)
        self.assertEquals(models.Cart.objects.get(
            user=self.user).id, anonymous_cart_id)


class TestRemoveFromCart(TestCase):

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
        models.CartLine.objects.create(
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


class TestCheckoutView(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = factories.UserFactory.create()
        cls.product = factories.ProductFactory.create()

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
        cls.form_data = {**shipping_data, **billing_data}

        cls.use_default_form_data = {key: '' for key in cls.form_data}
        cls.use_default_form_data['shipping-is_default'] = False
        cls.use_default_form_data['billing-is_default'] = False
        cls.use_default_form_data['shipping-use_default'] = True
        cls.use_default_form_data['billing-use_default'] = True

    def setUp(self):
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


class TestCouponView(TestCase):

    def setUp(self):
        self.user = factories.UserFactory.create()
        product = factories.ProductFactory.create()

        self.client.force_login(self.user)
        self.client.get(product.get_add_to_cart_url())

        self.coupon = models.Coupon.objects.create(
            code='MINUS5', amount=5)

        cart = models.Cart.objects.get(user=self.user)
        self.cost_before_coupon = cart.get_total()

    def test_enter_valid_coupon(self):
        post_data = {'coupon-code': 'MINUS5'}

        response = self.client.post(reverse('games:add-coupon'), post_data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("games:checkout"))

        cart = models.Cart.objects.get(user=self.user)
        self.assertEquals(cart.coupon, self.coupon)
        self.assertEquals(
            cart.get_total(),
            self.cost_before_coupon - self.coupon.amount
        )

    def test_enter_invalid_coupon(self):
        post_data = {'coupon-code': 'INVALID_CODE'}

        response = self.client.post(reverse('games:add-coupon'), post_data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("games:checkout"))

        cart = models.Cart.objects.get(user=self.user)
        self.assertEquals(cart.coupon, None)


class TestPaymentView(TestCase):

    def setUp(self):
        self.user = factories.UserFactory.create()

    def test_redirect_payment_view_works(self):
        # Redirect user if not authenticated
        response = self.client.get(reverse('games:payment'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '{0}?next={1}'.format(
            reverse("account_login"), reverse("games:payment")))

        self.client.force_login(self.user)
        self.assertEquals(models.Cart.objects.filter(
            user=self.user).count(), 0)

        # Redirect user if no open Cart
        response = self.client.get(reverse('games:payment'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("games:home"))

        models.Cart.objects.create(user=self.user)
        self.assertEquals(models.Cart.objects.filter(
            user=self.user).count(), 1)

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
        # response = self.client.post(reverse('games:payment'))
        # self.assertEqual(response.status_code, 302)
        # self.assertRedirects(response, reverse("games:home"))

        models.Order.objects.all().update(
            status=models.Order.PAID)

        response = self.client.get(reverse('games:payment'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("games:home"))


class TestSearchView(TestCase):

    def setUp(self):
        self.product = models.Product.objects.create(
            name='Call of Duty Modern Warfare',
            price=Decimal(12.99),
            slug='call-of-duty-modern-warfare',
        )

    def test_blank_query_redirects(self):
        response = self.client.get(reverse('games:search'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("games:home"))

    def test_search_works(self):
        response = self.client.get(
            '{0}?query={1}'.format(reverse('games:search'),
                                   'modern'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'search.html')
        self.assertContains(response, self.product.name)


class TestIsStaffMixin(TestCase):

    def test_is_staff_mixin(self):
        user1, user2 = factories.UserFactory.create_batch(2)
        user2.is_staff = True
        user2.save()

        # unauthenticated user redirects
        response = self.client.get(reverse('games:orders-per-day'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("games:home"))

        # not staff user redirects
        self.client.force_login(user1)
        response = self.client.get(reverse('games:orders-per-day'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("games:home"))

        # staff user has access
        self.client.force_login(user2)
        response = self.client.get(reverse('games:orders-per-day'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'orders_per_day.html')


class TestLoggedOpenCartExistsMixin(TestCase):

    def test_not_logged_redirects(self):
        user = factories.UserFactory.create()

        # unauthenticated user redirects
        response = self.client.get(reverse('games:checkout'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            '{0}?next=/{1}'.format(
                reverse("account_login"),
                'checkout/'
            )
        )

        # without cart user redirects
        self.client.force_login(user)
        response = self.client.get(reverse('games:checkout'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("games:home"))
