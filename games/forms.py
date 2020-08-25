import logging
from django import forms
from django.forms import inlineformset_factory
from django_countries.widgets import CountrySelectWidget
from . import models
from .tasks import contact_us_form_filled


logger = logging.getLogger(__name__)


CartLineFormSet = inlineformset_factory(
    models.Cart,
    models.CartLine,
    fields=("quantity",),
    extra=0,
)


class ContactUsForm(forms.Form):
    name = forms.CharField(label='Your name', max_length=100)
    message = forms.CharField(
        max_length=600,
        widget=forms.Textarea
    )

    def send_mail(self):
        logger.info("Sending email to customer service")
        contact_us_form_filled.delay(self.cleaned_data)


class AddressForm(forms.ModelForm):
    use_default = forms.BooleanField(initial=False, required=False)

    class Meta:
        model = models.Address
        exclude = ['user', 'address_type']
        labels = {
            'street_address': 'Address',
            'apartment_address': 'Address 2 (optional)',
            'is_default': 'Save as default',
        }
        widgets = {
            'street_address': forms.TextInput(
                attrs={'placeholder': '1234 Main St'}),
            'apartment_address': forms.TextInput(
                attrs={'placeholder': 'Apartment or Suite'}),
            'country': CountrySelectWidget(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].required = False
        self.fields['use_default'].label = 'Use my default address:'

    def validate_input(self, values):
        for field in values:
            if field == '':
                return False
        return True


class CouponForm(forms.ModelForm):

    class Meta:
        model = models.Coupon
        fields = ['code']
        labels = {'code': ''}

        widgets = {'code': forms.TextInput(
            attrs={'placeholder': 'Promo code'})
        }


class SearchForm(forms.Form):
    query = forms.CharField()
