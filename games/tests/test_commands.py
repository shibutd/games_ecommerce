from io import StringIO
import tempfile
from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from games import models, factories

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

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


class TestMockOrders(TestCase):

    def setUp(self):
        self.out = StringIO()
        self.args = 3

    def test_no_products_raise_exception(self):
        self.assertEqual(models.Product.objects.count(), 0)

        with self.assertRaises(Exception) as context:
            call_command('mock_orders', self.args, stdout=self.out)

        self.assertTrue('To create orders there must be products specified'
                        in str(context.exception))

    def test_no_users_create_three_users(self):
        user_model = get_user_model()
        factories.ProductFactory.create_batch(5)

        self.assertEqual(user_model.objects.count(), 0)
        call_command('mock_orders', self.args, stdout=self.out)

        self.assertEqual(user_model.objects.count(), 3)

    def test_create_mock_orders(self):
        factories.ProductFactory.create_batch(5)
        self.assertEqual(models.Product.objects.count(), 5)

        call_command('mock_orders', self.args, stdout=self.out)

        self.assertEqual(models.Order.objects.count(), self.args)
        self.assertEqual(models.Order.objects.filter(
            status=models.Order.PAID).count(), self.args)

        orders = models.Order.objects.all()

        expected_out = "Creating mock orders:\n"
        for order in orders:
            expected_out += 'Order id: {0}, user: {1}, number of lines: {2}\n'.format(
                order.id, order.user.email, len(order.lines.all()))

        self.assertEqual(self.out.getvalue(), expected_out)
