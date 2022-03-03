from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse


class CoreURLTests(TestCase):
    def test_error_page(self):
        response = self.client.get('/page_does_not_exist404/')

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')

    def test_csrf_failure(self):
        csrf_client = Client(enforce_csrf_checks=True)
        response = csrf_client.post(reverse('users:signup'))
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertTemplateUsed(response, 'core/403csrf.html')
