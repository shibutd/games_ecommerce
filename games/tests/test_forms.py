from django.test import TestCase
from django.core import mail
from .. import forms


class TestForm(TestCase):

    def test_valid_contact_us_form_sends_email(self):
        form = forms.ContactUsForm({
            'name': "Luke Skywalker",
            'message': "Hi there"
        })
        self.assertTrue(form.is_valid())
        # self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject, 'Message from Games4Everyone')

    def test_invalid_contact_us_form(self):
        form = forms.ContactUsForm({'message': "Hi there"})
        self.assertFalse(form.is_valid())
