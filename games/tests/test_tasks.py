from datetime import timedelta
from django.test import TestCase, override_settings
from django.core import mail
from django.utils import timezone
from .. import models, factories, tasks


class TestCeleryTask(TestCase):

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_order_created(self):
        user = factories.UserFactory.create()
        order = models.Order.objects.create(user=user)

        task = tasks.order_created.delay(order.pk)

        self.assertEqual(task.get(), 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject,
                         'Order nr. {}'.format(order.pk))
        # self.assertEqual(mail.outbox[0].message,
        #                  'You have successfully placed an order.\n'
        #                  + 'Your order ID is {}'.format(order.pk))

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_contact_us_form_filled(self):
        form_data = {'name': "Luke Skywalker",
                     'message': "Hi there"}
        task = tasks.contact_us_form_filled.delay(form_data)

        self.assertEqual(task.get(), 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject,
                         'Message from "Contact Us" form')
        # self.assertEqual(
        #     mail.outbox[0].message, 'From: {0}\n\n{1}'.format(
        #         form_data.get('name'), form_data.get('message')))

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_delete_unactive_carts(self):
        user1, user2 = factories.UserFactory.create_batch(2)
        user1.last_login = timezone.now()
        user1.save()
        user2.last_login = timezone.now() - timedelta(days=15)
        user2.save()

        models.Cart.objects.create(user=user1)
        models.Cart.objects.create(user=user2)

        self.assertEqual(models.Cart.objects.count(), 2)

        tasks.delete_unactive_carts.delay()

        self.assertEqual(models.Cart.objects.count(), 1)
        self.assertEqual(models.Cart.objects.filter(
            user=user2).count(), 0)
