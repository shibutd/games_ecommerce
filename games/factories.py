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


class ProductImageFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = models.ProductImage

    product = factory.SubFactory(ProductFactory)
    image = factory.django.ImageField(
        filename='example.jpg', width=1000, height=1000, color='blue')

class AddressFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = models.Address

    street_address = factory.Faker('address')
    zip_code = factory.Sequence(lambda n: '000{}'.format(n))
    city = factory.Faker('city')
    country = 'US'
    address_type = models.Address.SHIPPING
    is_default = False


class PaymentFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = models.Payment

    amount = factory.fuzzy.FuzzyDecimal(10.0, 100.0, 2)


class OrderLineFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = models.OrderLine


class OrderFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = models.Order

    user = factory.SubFactory(UserFactory)
    payment = factory.SubFactory(PaymentFactory)
