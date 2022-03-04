import shutil
import tempfile
from math import ceil

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from yatube.settings import POSTS_PER_PAGE

from ..models import Post, Group, Comment, Follow

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPageTests(TestCase):

    def setUp(self):
        cache.clear()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='test_user')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

        cls.author = User.objects.create_user(username='author')
        cls.authorized_author = Client()
        cls.authorized_author.force_login(cls.author)

        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

        cls.test_group = Group.objects.create(
            title='test group title',
            slug='test_group_title',
            description='test_group_description'
        )
        cls.test_post = Post.objects.create(
            text='test post' * 4,
            author=cls.user,
            group=cls.test_group,
            image=uploaded
        )
        cls.test_comment_test_post = Comment.objects.create(
            text='test comment test post',
            author=cls.user,
            post=cls.test_post
        )

        cls.slug = cls.test_group.slug
        cls.username = cls.user.username
        cls.post_id = cls.test_post.id

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def page_post_object_context_validate(self, response):
        test_object = response.context['page_obj'][0]
        post_fields = {
            test_object.id: 1,
            test_object.text: 'test post' * 4,
            test_object.author.username: 'test_user',
            test_object.group.title: 'test group title',
            test_object.image: 'posts/small.gif',
        }
        for value, expected in post_fields.items():
            with self.subTest(value=value):
                self.assertEqual(value, expected)

    def test_authorized_client_follows_users(self):
        author = self.author
        user = self.user

        follow_count = Follow.objects.all().count()

        self.authorized_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': author.username}
                    )
        )

        map_exists = Follow.objects.filter(author=author, user=user).exists()

        self.assertEqual(Follow.objects.all().count(), follow_count + 1)
        self.assertTrue(map_exists)

    def test_authorized_client_unfollows_users(self):
        author = self.author
        user = self.user

        Follow.objects.create(author=author, user=user)
        self.authorized_client.get(
            reverse('posts:profile_unfollow',
                    kwargs={'username': author.username}
                    )
        )

        map_exists = Follow.objects.filter(author=author, user=user).exists()

        self.assertFalse(map_exists)

    def test_follower_get_followed_author_post(self):
        author = self.author
        user = self.user
        follow_post_text = 'follow_test'

        # Must be in /follow/ for user
        Post.objects.create(text=follow_post_text, author=author)

        # Must not be in /follow/ for user
        Post.objects.create(text=follow_post_text, author=user)

        response = self.authorized_client.get(reverse('posts:follow_index'))
        follow_post_list = response.context.get('page_obj')

        self.assertFalse(follow_post_list)

        Follow.objects.create(author=author, user=user)
        response = self.authorized_client.get(reverse('posts:follow_index'))
        follow_post_list = response.context.get('page_obj').object_list
        expected_follow_post = Post.objects.get(text=follow_post_text,
                                                author=author
                                                )
        expected_follow_post_list = [expected_follow_post, ]

        self.assertEqual(follow_post_list, expected_follow_post_list)

    def test_pages_use_correct_template(self):
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug': self.slug}
                    ): 'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': self.username}
                    ): 'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post_id}
                    ): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post_id}
                    ): 'posts/create_post.html',
            reverse('posts:follow_index'): 'posts/follow.html',
        }
        for reverse_name, template in templates_pages_names.items():
            response = self.authorized_client.get(reverse_name)
            self.assertTemplateUsed(response, template)

    def test_index_page_shows_correct_context(self):
        response = (self.authorized_client.get(reverse('posts:index')))
        self.assertEqual(response.context.get('title'),
                         'Последние обновления на сайте'
                         )
        self.assertEqual(response.context.get('description'),
                         'Это главная страница проекта Yatube'
                         )

    def test_index_page_object_shows_correct_context(self):
        response = self.authorized_client.get(reverse('posts:index'))
        self.page_post_object_context_validate(response)

    def test_group_posts_page_shows_correct_context(self):
        response = (self.authorized_client.
                    get(reverse('posts:group_list',
                                kwargs={'slug': self.test_group.slug}
                                )
                        )
                    )
        self.assertEqual(response.context.get('group').title,
                         'test group title'
                         )

    def test_group_posts_object_shows_correct_context(self):
        response = (self.authorized_client.
                    get(reverse('posts:group_list',
                                kwargs={'slug': self.test_group.slug}
                                )
                        )
                    )
        self.page_post_object_context_validate(response)

    def test_profile_page_shows_correct_context(self):
        response = (self.authorized_client.
                    get(reverse('posts:profile',
                                kwargs={'username': self.test_post.author}
                                )
                        )
                    )
        self.assertEqual(response.context.get('posts_counter'), 1)
        self.assertEqual(response.context.get('author').username, 'test_user')

    def test_profile_page_object_shows_correct_context(self):
        response = (self.authorized_client.
                    get(reverse('posts:profile',
                                kwargs={'username': self.test_post.author}
                                )
                        )
                    )
        self.page_post_object_context_validate(response)

    def test_post_detail_page_shows_correct_context(self):
        response = (self.authorized_client.
                    get(reverse('posts:post_detail',
                                kwargs={'post_id': self.post_id}
                                )
                        )
                    )

        title = response.context.get('title')
        expected_title = ('test post' * 4)[:30]

        posts_counter = response.context.get('posts_counter')

        self.assertEqual(title, expected_title)
        self.assertEqual(posts_counter, 1)

    def test_post_detail_object_shows_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post_id}
                    )
        )
        test_object = response.context.get('post')

        post_text_0 = test_object.text
        post_author_0 = test_object.author.username
        post_group_0 = test_object.group.title
        text_comment_0 = self.test_comment_test_post.text
        post_comment_0 = test_object.parent_post.get(text=text_comment_0).text

        self.assertEqual(post_text_0, 'test post' * 4)
        self.assertEqual(post_author_0, 'test_user')
        self.assertEqual(post_group_0, 'test group title')
        self.assertEqual(post_comment_0, 'test comment test post')

    def test_group_posts_object_shows_correct_group(self):
        wrong_test_group = Group.objects.create(
            title='wrong test group title',
            slug='wrong_test_group_title',
            description='wrong_test_group_description'
        )

        response = (self.authorized_client.
                    get(reverse('posts:group_list',
                                kwargs={'slug': self.test_group.slug}
                                )
                        )
                    )
        test_object = response.context.get('page_obj')[0]

        post_group_0 = test_object.group.title
        post_wrong_group_0 = wrong_test_group.title

        self.assertNotEqual(post_group_0, post_wrong_group_0)

    def test_post_create_page_shows_correct_context(self):
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.CharField,
            'group': forms.ModelChoiceField
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_shows_correct_form_context(self):
        response = (self.authorized_client.
                    get(reverse('posts:post_edit',
                                kwargs={'post_id': self.post_id}
                                )
                        )
                    )
        form_fields = {
            'text': forms.CharField,
            'group': forms.ModelChoiceField
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_object_shows_correct_context(self):
        response = (self.authorized_client.
                    get(reverse('posts:post_edit',
                                kwargs={'post_id': self.post_id}
                                )
                        )
                    )
        test_object = response.context.get('post')

        post_text_0 = test_object.text
        post_author_0 = test_object.author.username
        post_group_0 = test_object.group.title

        self.assertEqual(post_text_0, 'test post' * 4)
        self.assertEqual(post_author_0, 'test_user')
        self.assertEqual(post_group_0, 'test group title')

    def test_post_edit_page_shows_correct_context(self):
        response = (self.authorized_client.
                    get(reverse('posts:post_edit',
                                kwargs={'post_id': self.post_id}
                                )
                        )
                    )
        self.assertTrue(response.context.get('is_edit'))


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='test_user')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

        cls.test_group = Group.objects.create(
            title='test group title',
            slug='test_group_title',
            description='test_group_description'
        )

        for i in range(0, 13):
            cls.test_post = Post.objects.create(
                text=f'test post {i}',
                author=cls.user,
                group=cls.test_group
            )

        cls.expected_number_of_last_page = (
            int(ceil(
                Post.objects.all().count() / POSTS_PER_PAGE)
                )
        )

        cls.expected_number_of_objects_on_last_page = (
            int(Post.objects.all().count() % POSTS_PER_PAGE))

    def test_index_first_page_contains_correct_number_of_records(self):
        cache.clear()
        response = self.client.get(reverse('posts:index'))
        number_of_posts = len(response.context['page_obj'])
        self.assertEqual(number_of_posts, POSTS_PER_PAGE)

    def test_index_last_page_contains_correct_number_of_records(self):
        response = (self.client.
                    get(reverse(
                        'posts:index'
                    ) + f'?page={self.expected_number_of_last_page}')
                    )
        number_of_posts = len(response.context['page_obj'])
        self.assertEqual(number_of_posts,
                         self.expected_number_of_objects_on_last_page
                         )

    def test_group_list_first_page_contains_correct_number_of_records(self):
        response = (self.client.
                    get(reverse('posts:group_list',
                                kwargs={'slug': self.test_group.slug}
                                )
                        )
                    )
        number_of_posts = len(response.context['page_obj'])
        self.assertEqual(number_of_posts, POSTS_PER_PAGE)

    def test_group_list_last_page_contains_correct_number_of_records(self):
        response = (self.authorized_client.
                    get(reverse(
                        'posts:group_list',
                        kwargs={'slug': self.test_group.slug}
                    ) + f'?page={self.expected_number_of_last_page}'
                    )
                    )
        number_of_posts = len(response.context['page_obj'])
        self.assertEqual(number_of_posts,
                         self.expected_number_of_objects_on_last_page
                         )

    def test_profile_first_page_contains_correct_number_of_records(self):
        response = (self.authorized_client.
                    get(reverse('posts:profile',
                                kwargs={'username': self.test_post.author}
                                )
                        )
                    )
        number_of_posts = len(response.context['page_obj'])
        self.assertEqual(number_of_posts, POSTS_PER_PAGE)

    def test_profile_last_page_contains_correct_number_of_records(self):
        response = (self.authorized_client.
                    get(reverse(
                        'posts:profile',
                        kwargs={'username': self.test_post.author}
                    ) + f'?page={self.expected_number_of_last_page}'
                    )
                    )
        number_of_posts = len(response.context['page_obj'])
        self.assertEqual(number_of_posts,
                         self.expected_number_of_objects_on_last_page
                         )


class PageCachingTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.author = User.objects.create_user(username='author')
        cls.post = Post.objects.create(
            text='text',
            author=cls.author
        )

    def test_index_page_is_caching(self):
        posts_count = Post.objects.all().count()
        content_before_delete = self.client.get(reverse('posts:index')).content
        Post.objects.get(id=1).delete()
        content_after_delete = self.client.get(reverse('posts:index')).content

        self.assertEqual(Post.objects.count(), posts_count - 1)
        self.assertEqual(content_before_delete, content_after_delete)

        cache.clear()
        content_after_cache_is_cleared = self.client.get(
            reverse('posts:index')
        ).content
        self.assertNotEqual(content_after_delete,
                            content_after_cache_is_cleared
                            )
