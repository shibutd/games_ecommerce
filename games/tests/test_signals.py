import os
import tempfile
from decimal import Decimal
from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib import auth
from django.core.files.images import ImageFile
from .. import models, factories


class TestSignal(TestCase):

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_thumbnails_are_generated_on_save(self):
        # Create product instance
        product = factories.ProductFactory()
        image_file = 'games/fixtures/product-sampleimages/Call_of_Duty_MW2.jpg'

        # Create ProductImage instance
        with open(image_file, 'rb') as f:
            image = models.ProductImage(
                product=product,
                image=ImageFile(f, name="cdmw.jpg"),
            )

            with self.assertLogs("games", level="INFO") as cm:
                image.save()

        # Ensure logs was displayed
        self.assertGreaterEqual(len(cm.output), 1)

        image.refresh_from_db()

        # Ensure saved thumbnail is thumbnail of ProductImage
        storage_path = os.path.join(tempfile.gettempdir(),
                                    'product-thumbnails',
                                    'cdmw.jpg')
        with open(storage_path, "rb") as f:
            expected_content = f.read()
            assert image.thumbnail.read() == expected_content

        # image.thumbnail.delete(save=False)
        # image.image.delete(save=False)

    def test_add_to_cart_login_merge_works(self):
        user1 = factories.UserFactory()
        product1, product2 = factories.ProductFactory.create_batch(2)

        # user1 = models.User.objects.create_user(
        #     "user1@a.com", "pw432joij")

        # cb = models.Product.objects.create(
        #     name="The cathedral and the bazaar",
        #     slug="cathedral-bazaar",
        #     price=Decimal("10.00"),
        # )
        # w = models.Product.objects.create(
        #     name="Microsoft Windows guide",
        #     slug="microsoft-windows-guide",
        #     price=Decimal("12.00"),
        # )

        cart = models.Cart.objects.create(user=user1)
        models.CartLine.objects.create(
            cart=cart, product=product1, quantity=2)

        response = self.client.get(
            reverse("games:add-to-cart", kwargs={"slug": product1.slug}))
        self.assertEqual(response.status_code, 302)

        self.client.force_login(user1)

        response = self.client.post(
            reverse("account_login"),
            {"email": user1.email, "password": ""},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            auth.get_user(self.client).is_authenticated)
        self.assertTrue(
            models.Cart.objects.filter(user=user1).exists())

        cart = models.Cart.objects.get(user=user1)
        self.assertEquals(cart.count(), 3)
