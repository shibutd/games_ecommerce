import os
import tempfile
from django.test import TestCase, override_settings
from django.core.cache import cache
from .. import models, factories


class TestThumbnailSignal(TestCase):

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_thumbnails_are_generated_on_save(self):
        # Create product instance
        filename = 'example.jpg'
        productimage = factories.ProductImageFactory.create(
            image__name=filename)
        productimage.refresh_from_db()
        # Ensure saved thumbnail is thumbnail of ProductImage
        storage_path = os.path.join(tempfile.gettempdir(),
                                    'product-thumbnails',
                                    filename)

        with open(storage_path, "rb") as f:
            expected_content = f.read()
            self.assertEqual(productimage.thumbnail.read(),
                             expected_content)

        productimage.thumbnail.delete(save=False)
        productimage.image.delete(save=False)

class TestCacheSignal(TestCase):

    def setUp(self):
        cache.clear()
        self.product = factories.ProductFactory.create()
        self.tag = models.ProductTag.objects.create(
            name='Playstation 4', slug='playstation-4')
        self.product.tags.add(self.tag)

        cache.set(self.tag.slug, 25)
        cache.set('all_tags', 26)
        cache.set('all_products', 28)

    def tearDown(self):
        cache.clear()

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
