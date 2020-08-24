from django.utils import timezone
from datetime import timedelta
from django.test import TestCase
from django.urls import reverse
from .. import factories, models


class TestAdminViews(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = factories.UserFactory.create()
        cls.user.is_staff = True
        cls.user.save()

    def test_orders_per_day(self):
        p1, p2, p3 = factories.PaymentFactory.create_batch(3)
        p1.date_paid = timezone.now() - timedelta(days=200)
        p1.save()
        p2.date_paid = timezone.now() - timedelta(days=60)
        p2.save()
        p3.date_paid = timezone.now() - timedelta(days=30)
        p3.save()

        o1 = factories.OrderFactory.create(
            payment=p1, status=models.Order.PAID)
        o2 = factories.OrderFactory.create(
            payment=p2, status=models.Order.PAID)
        o3 = factories.OrderFactory.create(
            payment=p3, status=models.Order.PAID)

        o2_date = o2.payment.date_paid.strftime('%Y-%m-%d')
        o3_date = o3.payment.date_paid.strftime('%Y-%m-%d')

        self.client.force_login(self.user)

        response = self.client.post(
            reverse('admin:orders-per-day'))
        self.assertEqual(response.status_code, 200)

        data = dict(zip(response.context["labels"],
                        response.context["values"]))

        self.assertEqual(len(data), 2)
        self.assertEqual(
            data, {o2_date: 1, o3_date: 1})

    def test_most_bought_products(self):
        p1, p2, p3 = factories.ProductFactory.create_batch(3)
        o1, o2, o3 = factories.OrderFactory.create_batch(
            3, status=models.Order.PAID)

        factories.OrderLineFactory.create_batch(
            2, order=o1, product=p1)
        factories.OrderLineFactory.create_batch(
            2, order=o1, product=p2)
        factories.OrderLineFactory.create_batch(
            2, order=o2, product=p1)
        factories.OrderLineFactory.create_batch(
            2, order=o2, product=p3)
        factories.OrderLineFactory.create_batch(
            2, order=o3, product=p1)
        factories.OrderLineFactory.create_batch(
            1, order=o3, product=p2)

        self.client.force_login(self.user)

        response = self.client.post(
            reverse('admin:most-bought-products'),
            {'period': "90"},
        )
        self.assertEqual(response.status_code, 200)

        data = dict(zip(response.context["labels"],
                        response.context["values"]))

        self.assertEqual(
            data, {p2.name: 3, p3.name: 2, p1.name: 6})
