from functools import wraps
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView, GenericAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.mixins import UpdateModelMixin
from rest_framework.decorators import api_view
from django.shortcuts import get_object_or_404
from django_filters import DateTimeFilter, ChoiceFilter
from django_filters.rest_framework import FilterSet
from ..models import Order, OrderLine, Cart, CartLine, Product
from .serializers import OrderSerializer, OrderLineSerializer, CartSerializer
from .permissions import IsStaff, IsOrderOwner
from .pagination import PageSizePagination


class OrderFilter(FilterSet):
    status = ChoiceFilter(choices=Order.STATUSES)
    from_date = DateTimeFilter(
        field_name='date_added', lookup_expr='gte')
    to_date = DateTimeFilter(
        field_name='date_added', lookup_expr='lte')

    class Meta:
        mmodel = Order
        fields = ('status',
                  'from_date',
                  'to_date')


class OrderList(ListAPIView):
    """
    Return list of user's orders.
    If user is staff return list of all existing orders.
    """
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = PageSizePagination
    permission_classes = [IsAuthenticated]
    filterset_class = OrderFilter
    search_fields = ('^user__email',)
    ordering_fields = ('date_added',)
    name = 'order-list'

    def get_queryset(self):
        queryset = self.queryset
        user = self.request.user
        if not user.is_staff:
            queryset = queryset.filter(user=user)
        return queryset


class OrderDetail(RetrieveAPIView):
    """
    Return details of user's order.
    """
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated, IsOrderOwner]
    name = 'order-detail'


class OrderLinePartialUpdate(UpdateModelMixin, GenericAPIView):
    """
    Update order's detail (status or quantity).
    """
    queryset = OrderLine.objects.all()
    serializer_class = OrderLineSerializer
    permission_classes = [IsStaff]
    name = 'order-lines'

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)


class IsUserStaff(APIView):
    """
    Return 'true' if user is staff, otherwise return 'false'.
    """
    name = 'is-user-staff'

    def get(self, request, *args, **kwargs):
        user = request.user
        content = {'is_staff': user.is_staff}
        return Response(content)


class CartList(ListAPIView):
    """
    Return list of user's carts.
    """
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    name = 'cart-list'

    def get_queryset(self):
        queryset = self.queryset
        user = self.request.user
        return queryset.filter(user=user)


# APIS FOR FUTHER FRONTEND ON REACT

@api_view(['POST'])
def add_to_cart(request, slug):
    """
    Add product to cart or icrease quantity if it's already in cart.
    """
    product = get_object_or_404(Product, slug=slug)
    cart = request.cart
    if not cart:
        if request.user.is_authenticated:
            user = request.user
        else:
            user = None
        cart = Cart.objects.create(user=user)
        request.session["cart_id"] = cart.id

    cartline, created = CartLine.objects.get_or_create(
        cart=cart, product=product)

    if not created:
        cartline.quantity += 1
        cartline.save()
    content = {'id': cartline.pk,
               'product_name': product.name,
               'product_slug': product.slug,
               'price': product.price,
               'discount_price': product.discount_price,
               'quantity': cartline.quantity}
    return Response(content, status=status.HTTP_200_OK)


def cartline_is_valid(func):
    """
    Decorator to check if product exists in cart.
    """
    @wraps(func)
    def wrapper(request, slug, *args, **kwargs):
        cart = request.cart
        if not cart:
            content = {'message': 'You have no active cart.'}
            return Response(content, status=status.HTTP_404_NOT_FOUND)

        product = get_object_or_404(Product, slug=slug)

        try:
            cartline = CartLine.objects.get(
                cart=cart, product=product)
        except CartLine.DoesNotExist:
            content = {'message': 'This item is not in your cart.'}
            return Response(content, status=status.HTTP_404_NOT_FOUND)

        kwargs['cartline'] = cartline
        kwargs['product'] = product
        return func(request, slug, *args, **kwargs)

    return wrapper


@api_view(['POST'])
@cartline_is_valid
def remove_single_from_cart(request, slug, cartline, product):
    """
    Remove one instance of product out of cart.
    """
    if cartline.quantity > 1:
        cartline.quantity -= 1
        cartline.save()
    content = {'product_name': product.name,
               'quantity': cartline.quantity}
    return Response(content, status=status.HTTP_200_OK)


@api_view(['POST'])
@cartline_is_valid
def remove_from_cart(request, slug, cartline, product):
    """
    Remove product out of cart.
    """
    cartline.delete()
    content = {'product_name': product.name}
    return Response(content, status=status.HTTP_200_OK)
