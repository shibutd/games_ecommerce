from django.urls import path
from .views import (OrderList, OrderLinePartialUpdate,
                    IsUserStaff, OrderDetail, CartList)

urlpatterns = [
    path('orders/', OrderList.as_view(),
         name=OrderList.name),
    path('orders/<int:pk>', OrderDetail.as_view(),
         name=OrderDetail.name),

    path('order-lines/<int:pk>', OrderLinePartialUpdate.as_view(),
         name=OrderLinePartialUpdate.name),

    path('is-user-staff/', IsUserStaff.as_view(),
         name=IsUserStaff.name),

    path('carts/', CartList.as_view(),
         name=CartList.name),


    # APIS FOR FUTHER FRONTEND ON REACT

    # path('add-to-cart/<slug>', add_to_cart,
    #      name='add-to-cart'),
    # path('remove-single-from-cart/<slug>', remove_single_from_cart,
    #      name='remove-single-from-cart'),
    # path('remove-from-cart/<slug>', remove_from_cart,
    #      name='remove-from-cart'),
]
