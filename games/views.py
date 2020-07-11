from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, DetailView, FormView
from django.views.generic.base import View
from . import forms, models


class HomePageView(ListView):
    """
    View class for showing Home page.
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
    View class for showing product's details.
    """
    template_name = 'product_detail.html'
    model = models.Product
    context_object_name = 'product'


class ContactUsView(FormView):
    """
    View class for 'Contact Us' form.
    """
    template_name = 'contact_us.html'
    form_class = forms.ContactUsForm
    success_url = reverse_lazy('games:home')

    def form_valid(self, form):
        form.send_mail()
        return super().form_valid(form)


class OrderSummaryView(View):
    """
    View class to manage selected products in cart.
    """

    def get(self, *args, **kwargs):
        cart = self.request.cart
        if not cart:
            messages.warning(self.request, 'Your cart is empty.')
            return redirect('games:home')

        context = {'cart': cart}
        return render(self.request, 'order_summary.html', context)


class CheckoutView(View):
    """
    View to enter shipping and billing addresses.
    """

    def get(self, request, *args, **kwargs):
        shipping_form = forms.AddressForm(prefix='shipping')
        billibg_form = forms.AddressForm(prefix='billing')
        context = {'formset': (shipping_form, billibg_form)}

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
        billibg_form = forms.AddressForm(request.POST, prefix='billing')

        if shipping_form.is_valid():
            shipping_address, message = self.get_address_from_form(
                shipping_form, models.Address.SHIPPING)
            if not shipping_address:
                messages.warning(request, message)
                return redirect('games:checkout')

        if billibg_form.is_valid():
            billing_address, message = self.get_address_from_form(
                billibg_form, models.Address.BILLING)
            if not billing_address:
                messages.warning(request, message)
                return redirect('games:checkout')

        # Creating order
        # del self.request.session['cart_id']
        # cart = self.request.cart
        # cart.create_order(shipping_address, billing_address)

        return redirect('games:home')

    def get_default_address_if_exists(self, address_type):
        default_address_qs = models.Address.objects.filter(
            user=self.request.user,
            address_type=address_type,
            is_default=True,
        )
        if default_address_qs.exists():
            return default_address_qs[0], True
        return '', False

    def get_address_from_form(self, form, address_type):
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


def check_cartline_is_valid(cart, slug):
    """
    Check if product exists in cart.
    """
    if not cart:
        return False
    product = get_object_or_404(models.Product, slug=slug)

    try:
        cartline = models.CartLine.objects.get(
            cart=cart, product=product)
    except models.CartLine.DoesNotExist:
        return False
    return cartline


def remove_single_from_cart(request, slug):
    """
    Remove one instance of product in cart by one.
    """
    cartline = check_cartline_is_valid(request.cart, slug)
    if cartline:
        if cartline.quantity > 1:
            cartline.quantity -= 1
            cartline.save()
        return redirect('games:order-summary')
    else:
        messages.warning(request, 'This item is not in your cart.')
        return redirect('games:home')


def remove_from_cart(request, slug):
    """
    Remove product from cart.
    """
    cartline = check_cartline_is_valid(request.cart, slug)
    if cartline:
        cartline.delete()
        return redirect('games:order-summary')
    else:
        messages.warning(request, 'This item is not in your cart.')
        return redirect('games:home')
