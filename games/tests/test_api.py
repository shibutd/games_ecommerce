from django.urls import reverse
from django.utils.http import urlencode
from rest_framework import status
from rest_framework.test import APITestCase
from games import factories
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
