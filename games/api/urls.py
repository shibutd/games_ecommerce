from django.urls import path
from .views import OrderList, OrderLinePartialUpdate, IsUserStaff, OrderDetail

urlpatterns = [
    path('orders/', OrderList.as_view(),
         name=OrderList.name),
    path('orders/<int:pk>', OrderDetail.as_view(),
         name=OrderDetail.name),

    path('order-lines/<int:pk>', OrderLinePartialUpdate.as_view(),
         name=OrderLinePartialUpdate.name),

    path('is-user-staff/', IsUserStaff.as_view(),
         name=IsUserStaff.name),

    # path('cart-lines/', CartLineList.as_view(),
    #      name=CartLineList.name),

    # path('carts/', CartList.as_view(),
    #      name=CartList.name),

    # path('orders/<int:pk>/', OrderDetail.as_view(),
    #      name=OrderDetail.name),
    # path('order-lines/<int:pk>/', OrderLineDetail.as_view(),
    #      name=OrderLineDetail.name),
]
