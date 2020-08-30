import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from games import models, factories


class Command(BaseCommand):
    """
    Implement 'mock_orders' command for creating mock orders
    for demonstration purposes.
    """
    help = 'Mock orders for demonstration in Games4Everyone'

    def add_arguments(self, parser):
        """
        Add command's arguments: 'number of orders'to create.
        """
        parser.add_argument("number_of_orders", type=int)

    def handle(self, *args, **options):
        self.stdout.write("Creating mock orders:")

        # getting products
        products = models.Product.objects.all()
        if not products:
            raise Exception('To create orders there must be products specified. \
Did not find any.')

        # getting or creating users
        users = get_user_model().objects.all()
        if not users:
            users = factories.UserFactory.create_batch(3)

        # creating mock orders
        for _ in range(options['number_of_orders']):
            user = random.choice(users)
            order = models.Order.objects.create(user=user)
            # creating orderlines
            orderlines = []
            total_price = 0
            # choose products for order
            order_products = random.sample(
                list(products),
                k=min(random.randint(1, 5), len(products))
            )
            for product in order_products:
                orderlines.append(
                    models.OrderLine(order=order, product=product))
                total_price += product.price

            models.OrderLine.objects.bulk_create(orderlines)
            # turn order into paid one
            payment = models.Payment.objects.create(
                user=user, amount=total_price)
            order.payment = payment
            order.status = models.Order.PAID
            order.save()

            self.stdout.write(
                'Order id: {0}, user: {1}, number of lines: {2}'.format(
                    order.id, user.email, len(orderlines)))
