from django import forms
from django.core.mail import send_mail


class ContactUsForm(forms.Form):
    name = forms.CharField(label='Your name', max_length=100)
    message = forms.CharField(
        max_length=600,
        widget=forms.Textarea
    )

    def send_mail(self):
        message = "From: {0}\n{1}".format(
            self.cleaned_data["name"],
            self.cleaned_data["message"],
        )
        send_mail(
            "Message from Games4Everyone contact-us form",
            message,
            "site@games4everyone.com",
            ["customerservice@games4everyone.com"],
            fail_silently=False,
        )
