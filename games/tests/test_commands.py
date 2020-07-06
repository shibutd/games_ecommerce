from io import StringIO
import tempfile
from django.core.management import call_command
from django.test import TestCase, override_settings
from .. import models


class TestImport(TestCase):

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_import_data(self):
        out = StringIO()
        args = ['games/fixtures/product-sample.csv',
                'games/fixtures/product-sampleimages/']

        call_command('import_data', *args, stdout=out)

        expected_out = ("Importing products\n"
                        "Products processed=3 (created=3)\n"
                        "Tags processed=17 (created=9)\n"
                        "Images processed=3\n")

        self.assertEqual(out.getvalue(), expected_out)
        self.assertEqual(models.Product.objects.count(), 3)
        self.assertEqual(models.ProductTag.objects.count(), 9)
        self.assertEqual(models.ProductImage.objects.count(), 3)
