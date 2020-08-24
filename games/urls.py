from django.urls import path, include
from django.views.generic import TemplateView
from . import views


app_name = 'games'

urlpatterns = [
    path('', views.HomePageView.as_view(), name='home'),
    path('product/<slug>',
         views.ProductDetailView.as_view(),
         name='product'),
    path('about-us/', TemplateView.as_view(template_name='about_us.html'),
         name='about-us'),
    path('contact-us/', views.ContactUsView.as_view(),
         name='contact-us'),
    path('search/', views.SearchView.as_view(), name='search'),
    path('order-dashboard/', TemplateView.as_view(template_name='dashboard.html'),
         name='orders-dashboard'),
    path('order-summary/', views.OrderSummaryView.as_view(),
         name='order-summary'),
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),
    path('add-coupon/', views.AddCouponView.as_view(),
         name='add-coupon'),
    path('payment/', views.PaymentView.as_view(),
         name='payment'),

    path('add_to_cart/<slug>', views.add_to_cart, name='add-to-cart'),
    path('remove_single_from_cart/<slug>', views.remove_single_from_cart,
         name='remove-single-from-cart'),
    path('remove_from_cart/<slug>', views.remove_from_cart,
         name='remove-from-cart'),

    path('api/', include('games.api.urls')),

]
