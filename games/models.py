from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.urls import reverse
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
    active = models.BooleanField(default=True)

    objects = ProductTagManager()

    def __str__(self):
        return self.name

    def natural_key(self):
        return (self.slug,)


class InStockManager(models.Manager):
    def in_stock(self):
        return self.filter(in_stock=True)


class Product(models.Model):
    name = models.CharField(max_length=60)
    description = models.TextField(blank=True)
    price = models.DecimalField(
        max_digits=6, decimal_places=2)
    discount_price = models.DecimalField(
        max_digits=6, decimal_places=2, blank=True, null=True)
    slug = models.SlugField(max_length=48)
    in_stock = models.BooleanField(default=True)
    date_updated = models.DateTimeField(auto_now=True)
    tags = models.ManyToManyField('ProductTag', blank=True)

    objects = InStockManager()

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('games:product',
                       kwargs={'slug': self.slug})

    def get_add_to_cart_url(self):
        return reverse('games:add-to-cart',
                       kwargs={'slug': self.slug})

    def get_remove_from_cart_url(self):
        return reverse('games:remove-from-cart',
                       kwargs={'slug': self.slug})


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
        return self.street_address

    def save(self, *args, **kwargs):
        if self.is_default:
            default_adresses = Address.objects.filter(
                user=self.user, address_type=self.address_type, is_default=True)
            default_adresses.update(is_default=False)
        super(Address, self).save(*args, **kwargs)


class Cart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE,
                             blank=True, null=True)
    coupon = models.ForeignKey(
        'Coupon', on_delete=models.SET_NULL, blank=True, null=True)

    def is_empty(self):
        return self.lines.all().count() == 0

    def count(self):
        return sum(i.quantity for i in self.lines.all())

    def get_total(self):
        total = 0
        for cart_line in self.lines.all():
            total += cart_line.get_total_product_price()
        if self.coupon:
            total -= self.coupon.amount
        return total

    def get_all_products(self):
        products = []
        for line in self.lines.select_related('product'):
            products.append(line.product.name)
        return products

    def create_order(self, shipping_address, billing_address):
        order = Order.objects.filter(
            user=self.user, status=Order.NEW).first()
        if order:
            order.shipping_address = shipping_address
            order.billing_address = billing_address
            order.save()
        else:
            order_data = {
                'user': self.user,
                'shipping_address': shipping_address,
                'billing_address': billing_address,
            }
            order = Order.objects.create(**order_data)

        return order

    def submit(self):
        order = Order.objects.filter(
            user=self.user, status=Order.NEW).first()
        for line in self.lines.select_related('product'):
            order_line_data = {
                'order': order,
                'product': line.product,
                'quantity': line.quantity,
            }
            OrderLine.objects.create(**order_line_data)

        return order


class CartLine(models.Model):
    cart = models.ForeignKey(
        'Cart', related_name='lines', on_delete=models.CASCADE)
    product = models.ForeignKey(
        'Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def get_total_product_price(self):
        price = self.product.discount_price or self.product.price
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
        on_delete=models.SET_NULL, blank=True, null=True
    )
    shipping_address = models.ForeignKey(
        'Address',
        related_name='shipping_address',
        on_delete=models.SET_NULL, blank=True, null=True
    )
    payment = models.ForeignKey(
        'Payment', on_delete=models.SET_NULL, blank=True, null=True)

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
        'Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    status = models.IntegerField(
        choices=STATUSES, default=PROCESSING)


class Payment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.SET_NULL,
                             blank=True, null=True)
    # method = models.IntegerField(choices=METHODS)
    amount = models.DecimalField(max_digits=6, decimal_places=2)
    date_paid = models.DateField(auto_now_add=True)

    def __str__(self):
        return '{0}, {1}'.format(self.date_paid, self.amount)
        # return '{0}, {1}'.format(self.method, self.amount)


class Coupon(models.Model):
    code = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=6, decimal_places=2)

    def __str__(self):
        return self.code
