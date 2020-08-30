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
                        "Products processed=15 (created=15)\n"
                        "Tags processed=80 (created=15)\n"
                        "Images processed=15\n")

        self.assertEqual(out.getvalue(), expected_out)
        self.assertEqual(models.Product.objects.count(), 15)
        self.assertEqual(models.ProductTag.objects.count(), 15)
        self.assertEqual(models.ProductImage.objects.count(), 15)
