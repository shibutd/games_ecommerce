from django.test import TestCase
from django.core import mail
from .. import forms


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
