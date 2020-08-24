from django.test import TestCase
from django.contrib.auth import get_user_model


class TestCustomUserTests(TestCase):

    def setUp(self):
        self.user_model = get_user_model()

    def test_create_user(self):
        user = self.user_model.objects.create_user(
            email='will@email.com',
            password='testpass123'
        )
        self.assertFalse(getattr(user, 'username'))
        self.assertEqual(user.email, 'will@email.com')
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self):
        admin_user = self.user_model.objects.create_superuser(
            email='superadmin@email.com',
            password='testpass123'
        )
        self.assertFalse(getattr(admin_user, 'username'))
        self.assertEqual(admin_user.email, 'superadmin@email.com')
        self.assertTrue(admin_user.is_active)
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)
