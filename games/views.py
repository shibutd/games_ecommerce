from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, DetailView, View, FormView
from . import forms, models


class HomePageView(ListView):
    template_name = "home.html"
    model = models.Product
    paginate_by = 3
    context_object_name = 'products'

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(active=True).order_by('name')


class ProductDetailView(DetailView):
    model = models.Product
    template_name = 'product_detail.html'
    context_object_name = 'product'


class ContactUsView(FormView):
    template_name = 'contact_us.html'
    form_class = forms.ContactUsForm
    success_url = reverse_lazy('games:home')

    def form_valid(self, form):
        form.send_mail()
        return super().form_valid(form)


class OrderSummaryView(View):

    def get(self, *args, **kwargs):
        cart = self.request.cart
        if not cart:
            messages.warning(self.request, 'Your cart is empty.')
            return redirect('games:home')

        context = {'cart': cart}
        return render(self.request, 'order_summary.html', context)


def add_to_cart(request, slug):
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


def manage_basket(request):
    cart = request.cart
    if not cart or cart.is_empty():
        return render(request, "basket.html", {"formset": None})

    if request.method == "POST":
        formset = forms.CartLineFormSet(
            request.POST, instance=request.cart)
        if formset.is_valid():
            formset.save()
    else:
        formset = forms.CartLineFormSet(
            instance=request.cart)

    return render(request, "basket.html", {"formset": formset})


def check_cartline_is_valid(cart, slug):
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
    cartline = check_cartline_is_valid(request.cart, slug)
    if cartline:
        cartline.delete()
        return redirect('games:order-summary')
    else:
        messages.warning(request, 'This item is not in your cart.')
        return redirect('games:home')
