import logging
import random
from functools import wraps
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, FormView, TemplateView
from django.views.generic.base import View
from django.contrib.auth.views import redirect_to_login
from django.contrib.postgres.search import (SearchVector, SearchQuery,
                                            SearchRank, TrigramSimilarity)
from django.core.cache import cache
from django.db import transaction
from django.db.models.functions import Greatest
from . import forms, models
from .mixins import LoggedOpenCartExistsMixin, IsStaffMixin, CartContextMixin
from .recommender import Recommender
from .tasks import order_created


logger = logging.getLogger(__name__)

r = Recommender()


class HomePageView(ListView):
    """
    Display Home page.
    """
    template_name = 'home.html'
    model = models.Product
    paginate_by = 8
    context_object_name = 'products'

    def get_queryset(self):
        tag = self.request.GET.get('tag')
        # Filter by tag if it is exitsts
        if tag and tag != 'all':
            # Check cache
            products = cache.get(tag)
            if not products:
                tag = get_object_or_404(models.ProductTag, slug=tag)
                products = self.model.objects.in_stock().prefetch_related(
                    'images').filter(tags=tag).order_by('name')
                cache.set(tag, products)
        # Otherwise return all in stock products
        else:
            products = cache.get('all_products')

            if not products:
                products = self.model.objects.in_stock().prefetch_related(
                    'images').order_by('name')
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


class ProductDetailView(View):
    """
    Display product's details.
    """

    def get(self, request, slug, *args, **kwargs):
        context = {}

        products = models.Product.objects.prefetch_related(
            'images', 'tags').order_by('name')
        product = products.get(slug=slug)
        context['product'] = product

        num_of_suggested = 3
        suggested_products = r.suggest_products(product, num_of_suggested)

        if not suggested_products:
            products = models.Product.objects.prefetch_related('images')
            suggested_products = random.sample(
                list(products),
                k=min(num_of_suggested, len(products))
            )

        context['suggested_products'] = suggested_products

        return render(request, 'product_detail.html', context)


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


class OrderSummaryView(CartContextMixin, View):
    """
    Manage products in cart.
    """

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        return render(request, 'order_summary.html', context)


class CheckoutView(LoggedOpenCartExistsMixin, CartContextMixin, View):
    """
    Enter shipping, billing addresses and applying coupons.
    """

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()

        shipping_form = forms.AddressForm(prefix='shipping')
        billing_form = forms.AddressForm(prefix='billing')
        couponform = forms.CouponForm(prefix='coupon')

        context.update({'shipping_form': shipping_form,
                        'billing_form': billing_form,
                        'couponform': couponform})

        address_types = [{'name': 'shipping_address',
                          'type': models.Address.SHIPPING},
                         {'name': 'billing_address',
                          'type': models.Address.BILLING}]

        for address in address_types:
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
                if len(results) == 0:
                    search_similarity = Greatest(
                        TrigramSimilarity('name', query),
                        TrigramSimilarity('description', query),
                    )
                    results = models.Product.objects.annotate(
                        similarity=search_similarity
                    ).filter(similarity__gt=0.2).order_by('-similarity')

                return render(request, 'search.html', {'form': form,
                                                       'query': query,
                                                       'results': results})
        return redirect('games:home')


class PaymentView(CartContextMixin, View):
    """
    Display payment form and process payment.
    """

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        return render(request, 'payment.html', context)

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
        # Delete cart
        del self.request.session['cart_id']
        cart.delete()

        # Send e-mail to the customer
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


class OrdersPerDayView(IsStaffMixin, TemplateView):
    """
    Admin panel for monitoring number of paid orders by day.
    """
    template_name = 'orders_per_day.html'


class MostBoughtProductsView(IsStaffMixin, TemplateView):
    """
    Admin panel for monitoring most bought products.
    """
    template_name = 'most_bought_products.html'


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
