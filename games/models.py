from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.urls import reverse
from django.core.validators import MinValueValidator
from django_countries.fields import CountryField


class CustomUserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """
        Create and save a CustomUser instance with the given email and
        password.
        """
        if not email:
            raise ValueError("Users must have an email address")

        user = self.model(
            email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """
        Create a simple user.
        """
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """
        Create a superuser.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")

        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    """
    Custom User class with email field instead of username.
    """
    username = None
    email = models.EmailField('email address', unique=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email


class ProductTagManager(models.Manager):
    """
     Manager for loading Tags using slug
    """

    def get_by_natural_key(self, slug):
        return self.get(slug=slug)


class ProductTag(models.Model):
    name = models.CharField(max_length=32)
    slug = models.SlugField(max_length=48)
    description = models.TextField(blank=True)
    active = models.BooleanField(default=True)

    objects = ProductTagManager()

    def __str__(self):
        return self.name

    def natural_key(self):
        return (self.slug,)


class ActiveManager(models.Manager):
    def active(self):
        return self.filter(active=True)


class Product(models.Model):
    name = models.CharField(max_length=60)
    description = models.TextField(blank=True)
    price = models.DecimalField(
        max_digits=6, decimal_places=2)
    discount_price = models.DecimalField(
        max_digits=6, decimal_places=2, blank=True, null=True)
    slug = models.SlugField(max_length=48)
    active = models.BooleanField(default=True)
    in_stock = models.BooleanField(default=True)
    date_updated = models.DateTimeField(auto_now=True)
    tags = models.ManyToManyField('ProductTag', blank=True)

    objects = ActiveManager()

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('games:product', kwargs={
            'slug': self.slug
        })

    def get_add_to_cart_url(self):
        return reverse('games:add-to-cart', kwargs={
            'slug': self.slug
        })

    def get_remove_from_cart_url(self):
        return reverse('games:remove-from-cart', kwargs={
            'slug': self.slug
        })


class ProductImage(models.Model):
    product = models.ForeignKey(
        'Product', related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to="product-images")
    thumbnail = models.ImageField(
        upload_to="product-thumbnails", null=True)


class Address(models.Model):
    SHIPPING = 10
    BILLING = 20
    ADDRESS_CHOICES = ((SHIPPING, 'Shipping'), (BILLING, 'Billing'))

    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    street_address = models.CharField(max_length=60)
    apartment_address = models.CharField(
        max_length=60, blank=True)
    zip_code = models.CharField(max_length=12)
    city = models.CharField(max_length=60)
    country = CountryField(
        multiple=False, blank_label='Choose...')
    address_type = models.IntegerField(
        choices=ADDRESS_CHOICES)
    is_default = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = 'Addresses'

    def __str__(self):
        return '{0}, {1}, {2}, {3}, {4}. {5}, {6}, {7}'.format(
            self.user.email,
            self.street_address,
            self.apartment_address,
            self.zip_code,
            self.city,
            self.country,
            self.address_type,
            self.is_default
        )

    def save(self, *args, **kwargs):
        if self.is_default:
            Address.objects.filter(user=self.user,
                                   address_type=self.address_type,
                                   is_default=True).update(is_default=False)
        super(Address, self).save(*args, **kwargs)


class Cart(models.Model):
    OPEN = 10
    SUBMITTED = 20
    STATUSES = ((OPEN, "Open"), (SUBMITTED, "Submitted"))
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE,
                             blank=True, null=True)
    status = models.IntegerField(choices=STATUSES, default=OPEN)

    def is_empty(self):
        return self.lines.all().count() == 0

    def count(self):
        return sum(i.quantity for i in self.lines.all())

    def get_total(self):
        total = 0
        for cart_line in self.lines.all():
            total += cart_line.get_total_product_price()
        return total

    def create_order(self, billing_address, shipping_address):
        if not self.user:
            reverse('account_login')
        #     raise exceptions.BasketException(
        #         "Cannot create order without user")
        # logger.info(
        #     "Creating order for basket_id=%d"
        #     ", shipping_address_id=%d, billing_address_id=%d",
        #     self.id,
        #     shipping_address.id,
        #     billing_address.id,
        # )

        order_data = {
            'user': self.user,
            'billing_address': billing_address,
            'shipping_address': shipping_address,
        }

        order = Order.objects.create(**order_data)
        for line in self.lines.all():
            order_line_data = {
                'order': order,
                'product': line.product,
                'quantity': line.quantity,
            }
            OrderLine.objects.create(**order_line_data)
        # logger.info(
        #     "Created order with id=%d and lines_count=%d",
        #     order.id,
        #     c,
        # )
        self.status = Cart.SUBMITTED
        self.save()
        return order


class CartLine(models.Model):
    cart = models.ForeignKey(
        'Cart', related_name='lines', on_delete=models.CASCADE)
    product = models.ForeignKey(
        'Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(
        default=1, validators=[MinValueValidator(1)])

    def get_total_product_price(self):
        if self.product.discount_price:
            price = self.product.discount_price
        else:
            price = self.product.price
        return price * self.quantity


class Order(models.Model):
    NEW = 10
    PAID = 20
    DONE = 30
    STATUSES = ((NEW, "New"), (PAID, "Paid"), (DONE, "Done"))

    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    status = models.IntegerField(choices=STATUSES, default=NEW)

    billing_address = models.ForeignKey(
        'Address',
        related_name='billing_address',
        on_delete=models.PROTECT, blank=True, null=True
    )
    shipping_address = models.ForeignKey(
        'Address',
        related_name='shipping_address',
        on_delete=models.PROTECT, blank=True, null=True
    )
    date_updated = models.DateTimeField(auto_now=True)
    date_added = models.DateTimeField(auto_now_add=True)


class OrderLine(models.Model):
    PROCESSING = 10
    SENT = 20
    RECEIVED = 30
    CANCELLED = 40
    STATUSES = (
        (PROCESSING, "Processing"),
        (SENT, "Sent"),
        (RECEIVED, "Received"),
        (CANCELLED, "Cancelled"),
    )
    order = models.ForeignKey(
        'Order', on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey(
        'Product', on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(
        default=1, validators=[MinValueValidator(1)])
    status = models.IntegerField(choices=STATUSES, default=PROCESSING)
