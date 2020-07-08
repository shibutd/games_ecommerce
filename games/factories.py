from django.conf import settings
import factory
import factory.fuzzy
from . import models


class UserFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = settings.AUTH_USER_MODEL
        django_get_or_create = ('email',)

    email = factory.Sequence(lambda n: 'testuser{}@example.com'.format(n))


class ProductFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = models.Product

    name = factory.Faker('name')
    slug = factory.Faker('slug')
    price = factory.fuzzy.FuzzyDecimal(10.0, 100.0, 2)


# class AddressFactory(factory.django.DjangoModelFactory):

#     class Meta:
#         model = models.Address


# class OrderLineFactory(factory.django.DjangoModelFactory):
#     class Meta:
#         model = models.OrderLine


# class OrderFactory(factory.django.DjangoModelFactory):
#     user = factory.SubFactory(UserFactory)

#     class Meta:
#         model = models.Order
