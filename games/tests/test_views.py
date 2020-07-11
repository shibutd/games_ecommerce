from django.test import TestCase
from django.urls import reverse, resolve
from .. import views, models, forms, factories
from django.contrib import auth
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

    def test_add_to_cart_loggedin_works(self):
        user1 = factories.UserFactory()
        product1, product2 = factories.ProductFactory.create_batch(2)

        self.client.force_login(user1)

        self.client.get(product1.get_add_to_cart_url())
        self.client.get(product1.get_add_to_cart_url())

        self.assertTrue(
            models.Cart.objects.filter(user=user1).exists())
        self.assertEquals(
            models.CartLine.objects.filter(
                cart__user=user1).count(), 1)

        self.client.get(
            reverse("games:add-to-cart", kwargs={"slug": product2.slug}))

        self.assertEquals(
            models.CartLine.objects.filter(
                cart__user=user1).count(), 2)

    def test_add_to_cart_login_merge_works(self):
        user1 = factories.UserFactory()
        product1, product2 = factories.ProductFactory.create_batch(2)
        # create cart of user1, add 2 cb
        cart = models.Cart.objects.create(user=user1)
        models.CartLine.objects.create(
            cart=cart, product=product1, quantity=2)
        # anonymous user with empty cart tries get to order-summary
        response = self.client.get(
            reverse("games:order-summary"))
        self.assertRedirects(response, reverse("games:home"))
        # anonymous user adds items to his Cart
        response = self.client.get(product2.get_add_to_cart_url())

        self.assertEquals(models.Cart.objects.count(), 2)
        self.assertEquals(
            models.Cart.objects.filter(
                user=user1).count(), 1)
        # anonymous user with not empty cart tries get to order-summary
        response = self.client.get(
            reverse("games:order-summary"))
        self.assertTemplateUsed(response, 'order_summary.html')

        self.client.force_login(user1)
        self.assertTrue(
            auth.get_user(self.client).is_authenticated)
        # cart of user and anonymous cart merged
        self.assertEquals(models.Cart.objects.count(), 1)

        response = self.client.get(product2.get_add_to_cart_url())

        self.assertEquals(models.Cart.objects.count(), 1)

    def test_user_can_save_shipping_and_billing_addresses(self):
        user = factories.UserFactory()

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
            'billing-street_address': '1234 Main St',
            'billing-apartment_address': '22',
            'billing-zip_code': '25121251',
            'billing-city': 'San Diego',
            'billing-country': 'US',
            'billing-is_default': True,
            'billing-use_default': False,
        }
        form_data = {**shipping_data, **billing_data}

        self.client.force_login(user)

        response = self.client.post(reverse('games:checkout'), form_data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("games:home"))

        self.assertEquals(len(models.Address.objects.filter(user=user)), 2)
        self.assertEquals(len(models.Address.objects.filter(
            user=user).filter(is_default=True)), 1)

        # test_if_user_can_have_only_one_unique_default_address_at_once
        models.Address.objects.filter(user=user).update(is_default=True)
        self.assertEquals(len(models.Address.objects.filter(
            user=user).filter(is_default=True)), 2)

        form_data['shipping-is_default'] = True
        form_data['billing-is_default'] = True
        response = self.client.post(reverse('games:checkout'), form_data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("games:home"))

        self.assertEquals(len(models.Address.objects.filter(
            user=user).filter(is_default=True)), 2)

        # test_user_can_use_default_address
        shipping_data = {
            'shipping-street_address': '',
            'shipping-apartment_address': '',
            'shipping-zip_code': '',
            'shipping-city': '',
            'shipping-country': '',
            'shipping-is_default': False,
            'shipping-use_default': True,
        }
        billing_data = {
            'billing-street_address': '',
            'billing-apartment_address': '',
            'billing-zip_code': '',
            'billing-city': '',
            'billing-country': '',
            'billing-is_default': False,
            'billing-use_default': True,
        }
        form_data = {**shipping_data, **billing_data}

        response = self.client.post(reverse('games:checkout'), form_data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("games:home"))

        # test_user_cant_use_not_existing_default_address
        models.Address.objects.filter(user=user, address_type=10).delete()
        response = self.client.post(reverse('games:checkout'), form_data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("games:checkout"))

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
