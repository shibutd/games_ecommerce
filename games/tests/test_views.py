from django.test import TestCase
from django.urls import reverse, resolve
from ..views import HomePageView


class HomePageTests(TestCase):

    def test_homepage_page_works(self):
        url = reverse('games:home')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'about_us.html')
        self.assertContains(response, 'BookTime')

    def test_homepage_url_resolves_homepageview(self):
        view = resolve('/')
        self.assertEqual(
            view.func.__name__,
            HomePageView.as_view().__name__
        )


class AboutUsPageTests(TestCase):

    def setUp(self):
        url = reverse('games:about-us')
        self.response = self.client.get(url)

    def test_about_us_page_works(self):
        url = reverse('about-us')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'about_us.html')
        self.assertContains(response, 'BookTime')
