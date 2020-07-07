from django.urls import path
from django.views.generic import TemplateView
from . import views


app_name = 'games'


urlpatterns = [
    path('', views.HomePageView.as_view(), name='home'),
    path('product/<slug>', views.ProductDetailView.as_view(), name='product'),

    path('about-us/',
         TemplateView.as_view(template_name='about_us.html'),
         name='about-us'),
    path('contact-us/',
         views.ContactUsView.as_view(template_name='contact_us.html'),
         name='contact-us'),

    path('order-summary/',
         views.OrderSummaryView.as_view(),
         name='order-summary'),

    path('basket/', views.manage_basket, name="basket"),

    path('add_to_cart/<slug>',
         views.add_to_cart,
         name='add-to-cart'),

    path('remove_single_from_cart/<slug>',
         views.remove_single_from_cart,
         name='remove-single-from-cart'),

    path('remove_from_cart/<slug>',
         views.remove_from_cart,
         name='remove-from-cart'),
]
