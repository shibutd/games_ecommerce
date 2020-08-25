from django.utils import timezone
from datetime import timedelta
from django.urls import reverse
from django.utils.http import urlencode
from rest_framework import status
from rest_framework.test import APITestCase
from games import factories, models
from games.api.views import (
    OrderList, OrderDetail, OrderLinePartialUpdate, IsUserStaff)


class TestOrder(APITestCase):

    def setUp(self):
        self.user1 = factories.UserFactory.create()
        self.user1.is_staff = True
        self.user1.save()
        self.user2 = factories.UserFactory.create()

        self.order1 = factories.OrderFactory.create(user=self.user1)
        self.order2 = factories.OrderFactory.create(user=self.user2)

        self.product = factories.ProductFactory.create()
        self.orderline = factories.OrderLineFactory.create(
            order=self.order1, product=self.product)

    def test_retrieve_order_list(self):
        url = '{0}?{1}'.format(
            reverse('games:{}'.format(OrderList.name)),
            urlencode({'ordering': '-date_added'}))

        self.client.force_login(self.user1)
        get_response = self.client.get(url, format='json')
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
        self.assertEqual(get_response.data['count'], 2)
        self.client.logout()

        self.client.force_login(self.user2)
        get_response = self.client.get(url, format='json')
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
        self.assertEqual(get_response.data['count'], 1)

    def test_retrieve_order_by_id(self):
        url_order1 = reverse('games:{}'.format(OrderDetail.name),
                             kwargs={'pk': self.order1.id})
        url_order2 = reverse('games:{}'.format(OrderDetail.name),
                             kwargs={'pk': self.order2.id})

        self.client.force_login(self.user1)
        get_response = self.client.get(url_order1, format='json')
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
        self.assertEqual(get_response.data['id'], self.order1.id)
        self.client.logout()

        self.client.force_login(self.user2)
        get_response = self.client.get(url_order2, format='json')
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
        self.assertEqual(get_response.data['id'], self.order2.id)

        get_response = self.client.get(url_order1, format='json')
        self.assertEqual(get_response.status_code,
                         status.HTTP_403_FORBIDDEN)

    def test_partial_update_orderline(self):
        url = reverse('games:{}'.format(OrderLinePartialUpdate.name),
                      kwargs={'pk': self.orderline.id})

        self.client.force_login(self.user1)
        get_response = self.client.patch(url, {'status': 20}, format='json')
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
        self.assertEqual(get_response.data['status'], 20)
        self.client.logout()

        self.client.force_login(self.user2)
        get_response = self.client.patch(url, {'status': 30}, format='json')
        self.assertEqual(get_response.status_code,
                         status.HTTP_403_FORBIDDEN)


class TestIsUserStaff(APITestCase):

    def test_is_user_staff(self):
        url = reverse('games:{}'.format(IsUserStaff.name))

        user1 = factories.UserFactory.create()
        user1.is_staff = True
        user1.save()
        user2 = factories.UserFactory.create()

        self.client.force_login(user1)
        get_response = self.client.get(url, format='json')
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
        self.assertTrue(get_response.data['is_staff'])
        self.client.logout()

        self.client.force_login(user2)
        get_response = self.client.get(url, format='json')
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
        self.assertFalse(get_response.data['is_staff'])


class TestOrdersPerDay(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = factories.UserFactory.create()
        cls.user.is_staff = True
        cls.user.save()

    def test_valid_period(self):
        p1, p2, p3 = factories.PaymentFactory.create_batch(3)
        p1.date_paid = timezone.now() - timedelta(days=200)
        p1.save()
        p2.date_paid = timezone.now() - timedelta(days=50)
        p2.save()
        p3.date_paid = timezone.now() - timedelta(days=20)
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

        data = [{'order_day': o3_date, 'order_num': 1}]

        get_response = self.client.get(
            reverse('games:api-orders-per-day',
                    kwargs={'period': 30}),
            format='json'
        )
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(get_response.data), 1)
        self.assertEqual(get_response.data, data)

        get_response = self.client.get(
            reverse('games:api-orders-per-day',
                    kwargs={'period': 60}),
            format='json'
        )
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(get_response.data), 2)

    def test_invalid_period(self):
        self.client.force_login(self.user)

        get_response = self.client.get(
            reverse('games:api-orders-per-day',
                    kwargs={'period': 27}),
            format='json'
        )
        self.assertEqual(get_response.status_code, status.HTTP_400_BAD_REQUEST)


class TestMostBoughtProducts(APITestCase):

    def test_most_bought_products(self):
        user = factories.UserFactory.create()
        user.is_staff = True
        user.save()

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

        self.client.force_login(user)

        get_response = self.client.get(
            reverse('games:api-most-bought-products',
                    kwargs={'period': "90"}),
            format='json'
        )
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
        self.assertCountEqual(
            get_response.data,
            [{'product_name': p2.name, 'purchase_num': 3},
             {'product_name': p3.name, 'purchase_num': 2},
             {'product_name': p1.name, 'purchase_num': 6}]
        )
