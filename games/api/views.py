from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView, GenericAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.mixins import UpdateModelMixin
from django_filters import DateTimeFilter, ChoiceFilter
from django_filters.rest_framework import FilterSet
from ..models import Order, OrderLine, CartLine
from .serializers import (OrderSerializer,
                          OrderLineSerializer)
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
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated, IsOrderOwner]
    name = 'order-detail'


class OrderLinePartialUpdate(UpdateModelMixin, GenericAPIView):
    queryset = OrderLine.objects.all()
    serializer_class = OrderLineSerializer
    permission_classes = [IsStaff]
    name = 'order-lines'

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)


class IsUserStaff(APIView):
    name = 'is-user-staff'

    def get(self, request, *args, **kwargs):
        user = request.user
        content = {'is_staff': user.is_staff}
        return Response(content)


# class CartLineList(ListAPIView):
#     queryset = CartLine.objects.all()
#     serializer_class = CartLineSerializer
#     # filterset_class = OrderFilter
#     # search_fields = ('^user__email',)
#     # ordering_fields = ('date_added',)
#     name = 'cart-line-list'

#     def get_queryset(self):
#         queryset = self.queryset
#         user = self.request.user
#         return queryset.filter(cart__user=user)

# class CartList(ListAPIView):
#     queryset = Cart.objects.all()
#     serializer_class = CartSerializer
    # filterset_class = OrderFilter
    # search_fields = ('^user__email',)
    # ordering_fields = ('date_added',)
    # name = 'cart-list'

    # def get_queryset(self):
    #     queryset = self.queryset
    #     user = self.request.user
    #     return queryset.filter(user=user)

# class OrderLineDetail(RetrieveAPIView):
#     queryset = OrderLine.objects.all()
#     serializer_class = OrderLineSerializer
#     name = 'orderline-detail'
