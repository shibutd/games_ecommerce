from __future__ import absolute_import, unicode_literals
from celery import task
from celery.decorators import periodic_task
from celery.schedules import crontab
from django.core.mail import send_mail
from django.utils import timezone
from .models import Order, Cart


@task
def order_created(order_id):
    """
    Task to send an e-mail notification when an order is
    successfully created.
    """
    order = Order.objects.get(pk=order_id)
    subject = 'Order nr. {}'.format(order.pk)
    message = 'You have successfully placed an order.\n' \
        + 'Your order ID is {}'.format(order.pk)
    mail_sent = send_mail(
        subject,
        message,
        'site@games4everyone.com',
        [order.user.email]
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


def timedelta_in_days(time):
    """
    Compute timedelta in days between cuurent time
    and given time.
    """
    timedelta = timezone.now() - time
    return timedelta.days


@periodic_task(run_every=crontab(hour=4,
                                 minute=30,
                                 day_of_week=[1, 4]))
def delete_unactive_carts():
    """
    Delete Carts if user was logged in more than 2 weeks ago.
    """
    carts = Cart.objects.select_related('user')
    for cart in carts:
        if timedelta_in_days(cart.user.last_login) >= 14:
            cart.delete()
