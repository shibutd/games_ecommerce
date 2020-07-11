import logging
from django import forms
from django.core.mail import send_mail
from django.forms import inlineformset_factory, formset_factory
from django_countries.widgets import CountrySelectWidget
from . import models


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

        message = "From: {0}\n{1}".format(
            self.cleaned_data["name"],
            self.cleaned_data["message"],
        )
        send_mail(
            "Message from contact-us form",
            message,
            "site@games4everyone.com",
            ["customerservice@games4everyone.com"],
            fail_silently=False,
        )


class AddressForm(forms.ModelForm):
    use_default = forms.BooleanField(initial=False, required=False)

    class Meta:
        model = models.Address
        exclude = ['user', 'address_type']
        # fields = [
        #     'user',
        #     'street_address',
        #     'apartment_address',
        #     'zip_code',
        #     'city',
        #     'country',
        #     'address_type',
        #     'is_default'
        # ]
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
            'address_type': forms.HiddenInput(),
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


# AddressFormSet = formset_factory(
#     AddressForm,
#     extra=2,
#     max_num=2,
#     min_num=1,
# )
