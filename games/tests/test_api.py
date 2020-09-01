from django.utils import timezone
from datetime import timedelta
from django.urls import reverse
from django.utils.http import urlencode
from rest_framework import status
from rest_framework.test import APITestCase
from games import factories, models
from games.api.views import (
    OrderList, OrderDetail, OrderLinePartialUpdate, IsUserStaff,
    CartList)


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


class TestCart(APITestCase):

    def setUp(self):
        self.user1, self.user2 = factories.UserFactory.create_batch(2)

        self.cart1 = factories.CartFactory.create(user=self.user1)
        self.cart2 = factories.CartFactory.create(user=self.user2)

    def test_retrieve_cart_list(self):
        url = reverse('games:{}'.format(CartList.name))

        self.client.force_login(self.user1)
        get_response = self.client.get(url, format='json')
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
        cart1 = get_response.data[0]
        self.assertEqual(len(get_response.data), 1)
        self.assertEqual(cart1['id'], self.cart1.id)

        self.client.logout()

        self.client.force_login(self.user2)
        get_response = self.client.get(url, format='json')
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
        cart2 = get_response.data[0]
        self.assertEqual(len(get_response.data), 1)
        self.assertEqual(cart2['id'], self.cart2.id)


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


class TestCartManipulation(APITestCase):

    def setUp(self):
        self.user = factories.UserFactory.create()
        self.product1, self.product2 = factories.ProductFactory.create_batch(2)
        self.cart = factories.CartFactory.create(user=self.user)

    def test_add_to_cart_create_cart(self):
        models.Cart.objects.all().delete()

        post_response = self.client.post(
            reverse('games:api-add-to-cart',
                    kwargs={'slug': self.product1.slug}),
            format='json'
        )
        self.assertEqual(post_response.status_code, status.HTTP_200_OK)
        self.assertEqual(models.Cart.objects.count(), 1)

    def test_add_to_cart_valid_product(self):
        self.assertEqual(self.cart.count(), 0)

        self.client.force_login(self.user)
        post_response = self.client.post(
            reverse('games:api-add-to-cart',
                    kwargs={'slug': self.product1.slug}),
            format='json'
        )
        self.assertEqual(post_response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.cart.count(), 1)

        post_response = self.client.post(
            reverse('games:api-add-to-cart',
                    kwargs={'slug': self.product1.slug}),
            format='json'
        )
        self.assertEqual(post_response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.cart.count(), 2)

    def test_add_to_cart_invalid_product(self):
        post_response = self.client.post(
            reverse('games:api-add-to-cart',
                    kwargs={'slug': 'invalid_slug'}),
            format='json'
        )
        self.assertEqual(post_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_remove_no_cart(self):
        models.Cart.objects.all().delete()

        self.client.force_login(self.user)
        post_response = self.client.post(
            reverse('games:api-remove-from-cart',
                    kwargs={'slug': self.product1.slug}),
            format='json'
        )
        self.assertEqual(post_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertCountEqual(
            post_response.data,
            {'error': 'You have no active cart.'}
        )

    def test_remove_cartline_is_not_valid(self):
        factories.CartLineFactory.create(
            cart=self.cart, product=self.product1)

        self.client.force_login(self.user)
        post_response = self.client.post(
            reverse('games:api-remove-from-cart',
                    kwargs={'slug': self.product2.slug}),
            format='json'
        )
        self.assertEqual(post_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertCountEqual(
            post_response.data,
            {'error': 'This item is not in your cart.'}
        )

    def test_remove_single_from_cart(self):
        factories.CartLineFactory.create(
            cart=self.cart, product=self.product1, quantity=3)
        factories.CartLineFactory.create(
            cart=self.cart, product=self.product2, quantity=1)

        self.client.force_login(self.user)
        post_response = self.client.post(
            reverse('games:api-remove-single-from-cart',
                    kwargs={'slug': self.product1.slug}),
            format='json'
        )
        self.assertEqual(post_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            post_response.data,
            {'product_name': self.product1.name, 'quantity': 2}
        )
        cartline1 = models.CartLine.objects.get(
            cart=self.cart, product=self.product1)
        self.assertEqual(cartline1.quantity, 2)

        post_response = self.client.post(
            reverse('games:api-remove-single-from-cart',
                    kwargs={'slug': self.product2.slug}),
            format='json'
        )
        self.assertEqual(post_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            post_response.data,
            {'product_name': self.product2.name, 'quantity': 1}
        )
        cartline2 = models.CartLine.objects.get(
            cart=self.cart, product=self.product2)
        self.assertEqual(cartline2.quantity, 1)

    def test_remove_from_cart(self):
        factories.CartLineFactory.create(
            cart=self.cart, product=self.product1, quantity=2)

        self.client.force_login(self.user)
        post_response = self.client.post(
            reverse('games:api-remove-from-cart',
                    kwargs={'slug': self.product1.slug}),
            format='json'
        )
        self.assertEqual(post_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            post_response.data,
            {'product_name': self.product1.name}
        )
        self.assertEqual(
            models.CartLine.objects.filter(cart=self.cart).count(), 0)
