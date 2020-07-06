import os
import tempfile
from decimal import Decimal
from django.test import TestCase, override_settings
from django.core.files.images import ImageFile
from .. import models


class TestSignal(TestCase):

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_thumbnails_are_generated_on_save(self):
        # Create product instance
        product = models.Product(
            name="Call of Duty",
            price=Decimal("10.00"),
        )
        product.save()

        image_file = 'games/fixtures/product-sampleimages/Call_of_Duty_MW2.png'

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
                                    'codc.jpg')
        with open(storage_path, "rb") as f:
            expected_content = f.read()
            assert image.thumbnail.read() == expected_content

        # image.thumbnail.delete(save=False)
        # image.image.delete(save=False)
