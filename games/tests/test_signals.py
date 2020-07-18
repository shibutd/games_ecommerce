import os
import tempfile
from django.test import TestCase, override_settings
from django.core.files.images import ImageFile
from django.core.cache import cache
from .. import models, factories


class TestSignal(TestCase):

    def setUp(self):
        cache.clear()
        self.product = factories.ProductFactory.create()
        self.tag = models.ProductTag.objects.create(
            name='Playstation 4', slug='playstation-4')
        self.product.tags.add(self.tag)

        cache.set(self.tag.slug, 25)
        cache.set('all_tags', 26)
        cache.set('all_products', 28)

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
            # with self.assertLogs("games", level="INFO") as cm:
            image.save()
        # Ensure logs was displayed
        # self.assertGreaterEqual(len(cm.output), 1)
        image.refresh_from_db()
        # Ensure saved thumbnail is thumbnail of ProductImage
        storage_path = os.path.join(tempfile.gettempdir(),
                                    'product-thumbnails',
                                    'cdmw.jpg')
        with open(storage_path, "rb") as f:
            expected_content = f.read()
            assert image.thumbnail.read() == expected_content

        image.thumbnail.delete(save=False)
        image.image.delete(save=False)

    def test_producttag_cache_clear_on_delete(self):
        tag_slug = self.tag.slug

        self.assertEqual(cache.get(tag_slug), 25)
        self.assertEqual(cache.get('all_tags'), 26)

        self.tag.delete()

        self.assertEqual(cache.get(tag_slug), None)
        self.assertEqual(cache.get('all_tags'), None)

    def test_producttag_cache_clear_on_save(self):
        self.assertEqual(cache.get('all_tags'), 26)

        models.ProductTag.objects.create(
            name='Playstation 5', slug='playstation-5')

        self.assertEqual(cache.get('all_tags'), None)

    def test_product_cache_clear_on_delete(self):
        tag_slug = self.tag.slug

        self.assertEqual(cache.get(tag_slug), 25)
        self.assertEqual(cache.get('all_products'), 28)

        self.product.delete()

        self.assertEqual(cache.get(tag_slug), None)
        self.assertEqual(cache.get('all_products'), None)

    def test_product_cache_clear_on_save(self):
        tag_slug = self.tag.slug

        self.assertEqual(cache.get(tag_slug), 25)
        self.assertEqual(cache.get('all_products'), 28)

        factories.ProductFactory.create()

        self.assertEqual(cache.get('all_products'), None)

    def test_product_cache_clear_on_m2m_changed(self):
        tag_slug = self.tag.slug

        self.assertEqual(cache.get(tag_slug), 25)
        self.assertEqual(cache.get('all_products'), 28)

        new_product = factories.ProductFactory.create()
        new_product.tags.add(self.tag)

        self.assertEqual(cache.get(tag_slug), None)
