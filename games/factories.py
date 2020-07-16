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

    name = factory.Sequence(lambda n: 'product {}'.format(n))
    slug = factory.Sequence(lambda n: 'product-{}'.format(n))
    price = factory.fuzzy.FuzzyDecimal(10.0, 100.0, 2)


class AddressFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = models.Address

    street_address = factory.Faker('address')
    zip_code = factory.Faker('zip')
    city = factory.Faker('city')
    country = 'US'
    address_type = 10
    is_default = False


# class OrderLineFactory(factory.django.DjangoModelFactory):
#     class Meta:
#         model = models.OrderLine


# class OrderFactory(factory.django.DjangoModelFactory):
#     user = factory.SubFactory(UserFactory)

#     class Meta:
#         model = models.Order
