import logging
import random
from functools import wraps
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404, resolve_url
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, FormView
from django.views.generic.base import View
from django.contrib.auth.mixins import AccessMixin
from django.contrib.auth.views import redirect_to_login
from django.contrib.postgres.search import (SearchVector, SearchQuery,
                                            SearchRank, TrigramSimilarity)
from django.core.cache import cache
from django.db import transaction
from . import forms, models
from .recommender import Recommender
from .tasks import order_created


logger = logging.getLogger(__name__)


class HomePageView(ListView):
    """
    Display Home page.
    """
    template_name = 'home.html'
    model = models.Product
    paginate_by = 4
    context_object_name = 'products'

    def get_queryset(self):
        tag = self.request.GET.get('tag')
        # Filter by tag if it is exitsts
        if tag and tag != 'all':
            # Check cache
            products = cache.get(tag)
            if not products:
                tag = get_object_or_404(
                    models.ProductTag, slug=tag)
                products = models.Product.objects.in_stock().filter(
                    tags=tag).order_by('name')
                cache.set(tag, products)
        # Otherwise return all in stock products
        else:
            products = cache.get('all_products')
            if not products:
                products = models.Product.objects.in_stock().order_by('name')
            cache.set('all_products', products)

        return products

    def get_context_data(self, **kwargs):
        # Display tags on home page
        context = super().get_context_data(**kwargs)
        # Check cache
        tags = cache.get('all_tags')
        if not tags:
            tags = list(models.ProductTag.objects.values_list(
                'name', 'slug'))
            cache.set('all_tags', tags)
        context['tags'] = random.sample(tags, k=min(5, len(tags)))
        return context


class ProductDetailView(DetailView):
    """
    Display product's details.
    """
    template_name = 'product_detail.html'
    model = models.Product
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        r = Recommender()
        product = self.get_object()
        suggested_products = r.suggest_products(product)
        if not suggested_products:
            suggested_products = random.choices(
                models.Product.objects.all(), k=3)
        context['suggested_products'] = suggested_products
        return context


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
    Deny access to unauthenticated user and user without OPEN cart.
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

        context = {'shipping_form': shipping_form,
                   'billing_form': billing_form,
                   'couponform': couponform}

        for address in [{'name': 'shipping_address',
                         'type': models.Address.SHIPPING},
                        {'name': 'billing_address',
                         'type': models.Address.BILLING}]:
            default_address, exists = self.get_default_address_if_exists(
                address['type'])
            if exists:
                context.update({address['name']: default_address})

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
        Return addres from AddressForm. If user checked 'use default'
        option, return default address if exists.
        """
        if form.cleaned_data['use_default']:
            default_address, exists = self.get_default_address_if_exists(
                address_type)
            if not exists:
                return '', 'You have no default {} address.'.format(
                    form.prefix)

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
    Apply valid coupon to cart.
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


class SearchView(View):
    """
    Search products.
    """

    def get(self, request, *args, **kwargs):
        query = request.GET.get('query')
        if query:
            form = forms.SearchForm(request.GET)
            if form.is_valid():
                query = form.cleaned_data['query']
                search_vector = SearchVector('name', 'description')
                search_query = SearchQuery(query)
                # Serch for query in products' names and descriptions
                results = models.Product.objects.annotate(
                    search=search_vector,
                    rank=SearchRank(search_vector, search_query)
                ).filter(search=search_query).order_by('-rank')
                # If serch return no results, check string similarities
                if not results:
                    try:
                        search_similarity = TrigramSimilarity('name', query) \
                            + TrigramSimilarity('description', query) \
                            + TrigramSimilarity('tags__name', query)
                        results = models.Product.objects.annotate(
                            similarity=search_similarity,
                        ).filter(similarity__gt=0.2).order_by('-similarity')
                    except Exception:
                        results = []

                return render(request, 'search.html', {'form': form,
                                                       'query': query,
                                                       'results': results})
        return redirect('games:home')


class PaymentView(View):
    """
    Display payment form and process payment.
    """

    def get(self, request, *args, **kwargs):
        return render(request, 'payment.html')

    @transaction.atomic
    def post(self, request, *args, **kwargs):
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
        # Send e-mail to the customer
        # Delete cart
        del self.request.session['cart_id']
        cart.delete()

        transaction.on_commit(lambda: order_created.delay(order.id))
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


def cartline_is_valid(func):
    """
    Decorator to check if product exists in cart.
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


@cartline_is_valid
def remove_single_from_cart(request, slug, cartline):
    """
    Remove one instance of product out of cart.
    """
    if cartline.quantity > 1:
        cartline.quantity -= 1
        cartline.save()
        return redirect('games:order-summary')

    return redirect('games:order-summary')


@cartline_is_valid
def remove_from_cart(request, slug, cartline):
    """
    Remove product out of cart.
    """
    cartline.delete()
    return redirect('games:order-summary')
