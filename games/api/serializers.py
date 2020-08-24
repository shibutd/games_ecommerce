from rest_framework.serializers import (ModelSerializer, ReadOnlyField,
                                        ChoiceField, DateTimeField)
from ..models import Order, OrderLine, Cart, CartLine


class OrderLineSerializer(ModelSerializer):
    product = ReadOnlyField(source='product.name')
    status = ChoiceField(
        choices=OrderLine.STATUSES)
    status_description = ReadOnlyField(
        source='get_status_display')

    class Meta:
        model = OrderLine
        fields = ('id',
                  'product',
                  'quantity',
                  'status',
                  'status_description')


class OrderSerializer(ModelSerializer):
    user = ReadOnlyField(source='user.email')
    shipping_address = ReadOnlyField(
        source='shipping_address.street_address')
    billing_address = ReadOnlyField(
        source='billing_address.street_address')
    date_added = DateTimeField(
        format="%Y-%m-%d %H:%M", read_only=True)
    status = ChoiceField(
        choices=OrderLine.STATUSES)
    status_description = ReadOnlyField(
        source='get_status_display')
    order_lines = OrderLineSerializer(
        many=True,
        read_only=True,
        source='lines'
    )

    class Meta:
        model = Order
        fields = ('id',
                  'user',
                  'shipping_address',
                  'billing_address',
                  'date_added',
                  'status',
                  'status_description',
                  'order_lines')


class CartLineSerializer(ModelSerializer):
    product_name = ReadOnlyField(
        source='product.name')
    product_slug = ReadOnlyField(
        source='product.slug')
    price = ReadOnlyField(
        source='product.price')
    discount_price = ReadOnlyField(
        source='product.discount_price')

    class Meta:
        model = CartLine
        fields = ('id',
                  'product_name',
                  'product_slug',
                  'price',
                  'discount_price',
                  'quantity',
                  )


class CartSerializer(ModelSerializer):
    cart_lines = CartLineSerializer(
        many=True,
        read_only=True,
        source='lines'
    )

    class Meta:
        model = Cart
        fields = ('id',
                  'coupon',
                  'cart_lines')
