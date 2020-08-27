from __future__ import absolute_import, unicode_literals
import logging
from datetime import timedelta
from celery import task
from django.core.mail import send_mail
from django.utils import timezone
from django.db.models import Subquery
from django.contrib.auth import get_user_model
from .models import Order, Cart
from .recommender import Recommender

logger = logging.getLogger(__name__).setLevel("INFO")


r = Recommender()


@task
def order_created(order_id):
    """
    Task to send an e-mail notification when an order is
    successfully created.
    """
    order = Order.objects.get(pk=order_id)
    products = [line.product for line in order.lines.all()]

    r.products_bought(products)

    subject = 'Order nr. {}'.format(order.pk)
    message = 'You have successfully placed an order.\n \
        + Your order ID is {}'.format(order.pk)
    mail_sent = send_mail(
        subject,
        message,
        'site@games4everyone.com',
        [order.user.email],
    )
    return mail_sent


@task
def contact_us_form_filled(form_data):
    """
    Task to send an e-mail message to customer service when
    'Contact us' form is filled.
    """
    subject = 'Message from "Contact Us" form'
    message = 'From: {0}\n\n{1}'.format(
        form_data.get('name'),
        form_data.get('message'),
    )
    mail_sent = send_mail(
        subject,
        message,
        'site@games4everyone.com',
        ['customerservice@games4everyone.com'],
    )
    return mail_sent


@task
def delete_unactive_carts():
    """
    Delete Carts if user was logged in more than 2 weeks ago.
    """
    two_weeks_ago = timezone.now() - timedelta(days=14)
    users = get_user_model().objects.filter(
        last_login__lt=two_weeks_ago)
    Cart.objects.select_related('user').filter(
        user__pk__in=Subquery(users.values('pk'))).delete()
