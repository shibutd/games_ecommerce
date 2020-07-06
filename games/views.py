from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import TemplateView, View, FormView
from . import forms


class HomePageView(TemplateView):
    template_name = 'home.html'


class ContactUsView(FormView):
    template_name = 'contact_us.html'
    form_class = forms.ContactUsForm
    success_url = reverse_lazy('games:home')

    def form_valid(self, form):
        form.send_mail()
        return super().form_valid(form)


class OrderSummaryView(View):

    def get(self, *args, **kwargs):
        # try:
        #     order = Order.objects.get(
        #         user=self.request.email, ordered=False)
        #     context = {
        #         'object': order
        #     }
        #     return render(self.request, 'order_summary.html', context)
        # except ObjectDoesNotExist:
        messages.warning(self.request, 'You have no active order.')
        return redirect('games:home')
