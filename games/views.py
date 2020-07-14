from functools import wraps
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404, resolve_url
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, FormView
from django.views.generic.base import View
from django.contrib.auth.mixins import AccessMixin
from django.contrib.auth.views import redirect_to_login
from . import forms, models


import logging
logger = logging.getLogger(__name__)


class HomePageView(ListView):
    """
    Display Home page.
    """
    template_name = "home.html"
    model = models.Product
    paginate_by = 3
    context_object_name = 'products'

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(active=True).order_by('name')


class ProductDetailView(DetailView):
    """
    Display product's details.
    """
    template_name = 'product_detail.html'
    model = models.Product
    context_object_name = 'product'


class ContactUsView(FormView):
    """
    Display 'Contact Us' form.
    """
    template_name = 'contact_us.html'
    form_class = forms.ContactUsForm
    success_url = reverse_lazy('games:home')

    def form_valid(self, form):
        form.send_mail()
        return super().form_valid(form)


class LoggedOpenCartExistsMixin(AccessMixin):
    """
    Deny access to unauthenticated user and user without
    OPEN cart.
    """
    permission_denied_message = 'Your cart is empty.'

    def handle_no_permission(self):
        messages.warning(self.request, self.permission_denied_message)
        return redirect('games:home')

    def dispatch(self, request, *args, **kwargs):
        # This will redirect to the login view
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path(),
                                     resolve_url(self.get_login_url()),
                                     self.get_redirect_field_name())
        if not request.cart:
            return self.handle_no_permission()

        return super().dispatch(request, *args, **kwargs)


class OrderSummaryView(View):
    """
    Manage products in cart.
    """

    def get(self, request, *args, **kwargs):
        return render(request, 'order_summary.html', {'cart': request.cart})


class CheckoutView(LoggedOpenCartExistsMixin, View):
    """
    Enter shipping and billing addresses and applying coupons.
    """

    def get(self, request, *args, **kwargs):
        shipping_form = forms.AddressForm(prefix='shipping')
        billing_form = forms.AddressForm(prefix='billing')
        couponform = forms.CouponForm(prefix='coupon')

        context = {'formset': (shipping_form, billing_form),
                   'couponform': couponform,
                   'DISPLAY_COUPON_FORM': True}

        default_shipping_address, exists = self.get_default_address_if_exists(
            models.Address.SHIPPING)
        if exists:
            context.update({'shipping_address': default_shipping_address})

        default_billing_address, exists = self.get_default_address_if_exists(
            models.Address.BILLING)
        if exists:
            context.update({'billing_address': default_billing_address})
        return render(request, 'checkout.html', context)

    def post(self, request, *args, **kwargs):
        shipping_form = forms.AddressForm(request.POST, prefix='shipping')
        billing_form = forms.AddressForm(request.POST, prefix='billing')

        if shipping_form.is_valid():
            shipping_address, message = self.get_address_from_form(
                shipping_form, models.Address.SHIPPING)
            if not shipping_address:
                messages.warning(request, message)
                return redirect('games:checkout')

        if billing_form.is_valid():
            billing_address, message = self.get_address_from_form(
                billing_form, models.Address.BILLING)
            if not billing_address:
                messages.warning(request, message)
                return redirect('games:checkout')
        # Creating order
        cart = request.cart
        cart.create_order(shipping_address, billing_address)

        return redirect('games:payment')

    def get_default_address_if_exists(self, address_type):
        """
        Check if user has default address of requested type.
        """
        default_address_qs = models.Address.objects.filter(
            user=self.request.user,
            address_type=address_type,
            is_default=True,
        )
        if default_address_qs.exists():
            return default_address_qs[0], True
        return '', False

    def get_address_from_form(self, form, address_type):
        """
        Return addres from AddressForm, if user checked 'use default'
        option, return default address if exists.
        """
        if form.cleaned_data['use_default']:
            default_address, exists = self.get_default_address_if_exists(address_type)
            if not exists:
                return '', 'You have no default {} address.'.format(form.prefix)

            return default_address, ''

        cleaned_data = form.cleaned_data
        if form.validate_input([cleaned_data['street_address'],
                                cleaned_data['zip_code'],
                                cleaned_data['city'],
                                cleaned_data['country']]):
            address = form.save(commit=False)
            address.user = self.request.user
            address.address_type = address_type
            address.save()
            return address, ''

        else:
            return '', 'Please fill in the required {} address fields.'.format(
                form.prefix)


class AddCouponView(LoggedOpenCartExistsMixin, View):
    """
    Apply coupon.
    """

    def post(self, request, *args, **kwargs):
        form = forms.CouponForm(request.POST, prefix='coupon')
        if form.is_valid():
            code = form.cleaned_data.get('code')
            try:
                coupon = models.Coupon.objects.get(code=code)
            except models.Coupon.DoesNotExist:
                messages.warning(self.request, 'This coupon does not exists.')
                return redirect('games:checkout')

            cart = request.cart
            cart.coupon = coupon
            cart.save()
            messages.success(request, 'Successfully added coupon.')
            return redirect('games:checkout')


class PaymentView(View):
    """
    Display payment form and process payment.
    """

    def get(self, request, *args, **kwargs):
        context = {
            'DISPLAY_COUPON_FORM': False,
        }
        return render(request, 'payment.html', context)

    def post(self, request, *args, **kwargs):
        del self.request.session['cart_id']
        cart = request.cart
        # Create the payment
        payment = models.Payment(
            user=request.user, amount=cart.get_total())
        payment.save()

        order = cart.submit()
        # Assign the payment to the order
        order.payment = payment
        order.status = models.Order.PAID
        order.save()

        messages.success(request, 'Your order was successfully paid!')
        return redirect('games:home')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())

        if not request.cart:
            messages.warning(self.request, 'Your cart is empty')
            return redirect('games:home')

        if not models.Order.objects.filter(
                user=request.user, status=models.Order.NEW).exists():
            messages.warning(request, 'Please assign address to your order.')
            return redirect('games:checkout')

        return super().dispatch(request, *args, **kwargs)


def add_to_cart(request, slug):
    """
    Add product to cart or icrease quantity if it's already in cart.
    """
    product = get_object_or_404(models.Product, slug=slug)
    cart = request.cart
    if not cart:
        if request.user.is_authenticated:
            user = request.user
        else:
            user = None
        cart = models.Cart.objects.create(user=user)
        request.session["cart_id"] = cart.id

    cartline, created = models.CartLine.objects.get_or_create(
        cart=cart, product=product)

    if not created:
        cartline.quantity += 1
        cartline.save()
        return redirect("games:order-summary")

    messages.success(request, 'This item added to your cart.')
    return redirect("games:product", slug=slug)


def manage_cart(request):
    cart = request.cart
    if not cart or cart.is_empty():
        return render(request, "cart.html", {"formset": None})

    if request.method == "POST":
        formset = forms.CartLineFormSet(
            request.POST, instance=request.cart)
        if formset.is_valid():
            formset.save()
    else:
        formset = forms.CartLineFormSet(
            instance=request.cart)

    return render(request, "cart.html", {"formset": formset})


def cartline_is_valid(func):
    """
    Check if product exists in cart.
    """
    @wraps(func)
    def wrapper(request, slug, *args, **kwargs):
        cart = request.cart
        if not cart:
            messages.warning(request, 'This item is not in your cart.')
            return redirect('games:product', slug=slug)

        product = get_object_or_404(models.Product, slug=slug)

        try:
            cartline = models.CartLine.objects.get(
                cart=cart, product=product)
        except models.CartLine.DoesNotExist:
            messages.warning(request, 'This item is not in your cart.')
            return redirect('games:product', slug=slug)

        kwargs['cartline'] = cartline
        return func(request, slug, *args, **kwargs)

    return wrapper


# def cartline_is_valid(cart, slug):
#     """
#     Check if product exists in cart.
#     """
#     if not cart:
#         return False
#     product = get_object_or_404(models.Product, slug=slug)

#     try:
#         cartline = models.CartLine.objects.get(
#             cart=cart, product=product)
#     except models.CartLine.DoesNotExist:
#         return False
#     return cartline


@cartline_is_valid
def remove_single_from_cart(request, slug, cartline):
    """
    Remove one instance of product out of cart.
    """
    if cartline.quantity > 1:
        cartline.quantity -= 1

        logger.debug(f'{cartline.quantity}')

        cartline.save()
        return redirect('games:order-summary')

    logger.debug(f'{cartline.quantity}')

    return redirect('games:order-summary')


@cartline_is_valid
def remove_from_cart(request, slug, cartline):
    """
    Remove product out of cart.
    """
    cartline.delete()
    return redirect('games:order-summary')
