from django.test import Client, TestCase


class StaticPagesURLTests(TestCase):
    def setUp(self):
        # Создаем неавторизованый клиент
        self.guest_client = Client()

    def test_about_url_exists_at_desired_location(self):
        response = self.guest_client.get('/about/author/')
        self.assertEqual(response.status_code, 200)

    def test_about_url_uses_correct_template(self):
        response = self.guest_client.get('/about/author/')
        self.assertTemplateUsed(response, 'about/about_author.html')

    def test_tech_url_exists_at_desired_location(self):
        response = self.guest_client.get('/about/tech/')
        self.assertEqual(response.status_code, 200)

    def test_tech_url_uses_correct_template(self):
        response = self.guest_client.get('/about/tech/')
        self.assertTemplateUsed(response, 'about/about_tech.html')
