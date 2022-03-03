from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class SmokeTest(TestCase):
    def test_homepage(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, HTTPStatus.OK)


class PostsURLTests(TestCase):

    def setUp(self):
        cache.clear()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.author = User.objects.create_user(username='author')
        cls.authorized_client_author = Client()
        cls.authorized_client_author.force_login(cls.author)

        cls.user = User.objects.create_user(username='test_user')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

        cls.test_group = Group.objects.create(
            title='test group title',
            slug='test_group_title',
            description='test_group_description'
        )
        cls.test_post = Post.objects.create(
            text='test post text',
            author=cls.author,
            group=cls.test_group
        )

        cls.slug = cls.test_group.slug
        cls.username = cls.user.username
        cls.post_id = cls.test_post.id

    def test_urls_exist_at_desired_location_for_anonimous(self):
        url_list = ['/',
                    f'/group/{self.slug}/',
                    f'/profile/{self.username}/',
                    f'/posts/{self.post_id}/',
                    ]
        for url in url_list:
            with self.subTest():
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_create_url_exists_at_desired_location_for_user(self):
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_url_exists_at_desired_location_for_author(self):
        response = (self.authorized_client_author
                    .get(f'/posts/{self.post_id}/edit/')
                    )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_redirect_anonimous_on_auth_login(self):
        url_list = ['/create/',
                    f'/posts/{self.post_id}/edit/',
                    f'/posts/{self.post_id}/comment/',
                    '/follow/'
                    ]
        for url in url_list:
            with self.subTest():
                response = self.client.get(url, follow=True)
                self.assertRedirects(
                    response, (f'/auth/login/?next={url}')
                )

    def test_post_edit_url_redirect_non_author_user_on_post_detail_URL(self):
        response = self.authorized_client.get(f'/posts/{self.post_id}/edit/')
        self.assertRedirects(
            response, (f'/posts/{self.post_id}/')
        )

    def test_urls_uses_correct_template(self):
        templates_url_names = {
            'posts/index.html': '/',
            'posts/group_list.html': f'/group/{self.slug}/',
            'posts/profile.html': f'/profile/{self.username}/',
            'posts/post_detail.html': f'/posts/{self.post_id}/',
            'posts/create_post.html': '/create/',
            'posts/follow.html': '/follow/'
        }
        for template, url in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_post_edit_url_uses_correct_template_for_author(self):
        response = (self.authorized_client_author.
                    get(f'/posts/{self.post_id}/edit/')
                    )
        template = 'posts/create_post.html'
        self.assertTemplateUsed(response, template)

    def test_url_doesnt_exists_returns_404(self):
        response = self.authorized_client.get('/404_not_found/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
