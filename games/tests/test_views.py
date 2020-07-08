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
            cart=cart, product=product1, quantity=2
        )

        # anon user with empty cart tries get to order-summary
        response = self.client.get(
            reverse("games:order-summary"))
        self.assertRedirects(response, reverse("games:home"))

        # anon user adds items to his Cart
        response = self.client.get(product2.get_add_to_cart_url())

        self.assertEquals(models.Cart.objects.count(), 2)
        self.assertEquals(
            models.Cart.objects.filter(
                user=user1).count(), 1)

        # anon user with not empty cart tries get to order-summary
        response = self.client.get(
            reverse("games:order-summary"))
        self.assertTemplateUsed(response, 'order_summary.html')

        self.client.force_login(user1)
        self.assertTrue(
            auth.get_user(self.client).is_authenticated)

        # cart of user and cart created while he was anon merged
        self.assertEquals(models.Cart.objects.count(), 1)

        response = self.client.get(product2.get_add_to_cart_url())

        self.assertEquals(models.Cart.objects.count(), 1)

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
