import logging
from django import forms
from django.core.mail import send_mail
from django.forms import inlineformset_factory
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
