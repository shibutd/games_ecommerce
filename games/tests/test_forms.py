from django.test import TestCase
from django.core import mail
from .. import forms
import logging


logger = logging.getLogger(__name__)

class TestForms(TestCase):

    def test_valid_contact_us_form_sends_email(self):
        form = forms.ContactUsForm({
            'name': "Luke Skywalker",
            'message': "Hi there"
        })
        self.assertTrue(form.is_valid())

        with self.assertLogs('games.forms', level='INFO') as cm:
            form.send_mail()

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject, 'Message from contact-us form')
        self.assertGreaterEqual(len(cm.output), 1)

    def test_invalid_contact_us_form(self):
        form = forms.ContactUsForm({'message': "Hi there"})
        self.assertFalse(form.is_valid())

    def test_valid_address_form(self):
        form_data = {
            'street_address': '1234 Main St',
            'apartment_address': '',
            'zip_code': '25121251',
            'city': 'San Diego',
            'country': 'US',
            'is_default': False,
            'use_default': False
        }
        form = forms.AddressForm()
        form_attrs = [form_data[attr] for attr in form_data
                      if attr in ('street_address', 'zip_code', 'city', 'country')]
        self.assertTrue(form.validate_input(form_attrs))

    def test_invalid_address_form(self):
        form_data = {
            'street_address': '',
            'apartment_address': '',
            'zip_code': '',
            'city': '',
            'country': '',
            'is_default': False,
            'use_default': False
        }
        form = forms.AddressForm()
        form_attrs = [form_data[attr] for attr in form_data
                      if attr in ('street_address', 'zip_code', 'city', 'country')]
        self.assertFalse(form.validate_input(form_attrs))
