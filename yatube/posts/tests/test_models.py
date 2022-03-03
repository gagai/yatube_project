from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostsAppModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(title='test title',
                                         slug='test-slug',
                                         description='test description'
                                         )
        cls.post = Post.objects.create(text='test_text',
                                       author=cls.user,
                                       group=(None)
                                       )

    def test_posts_have_correct_object_name(self):
        post = PostsAppModelTest.post
        expected_post_name = post.text[:15]
        self.assertEqual(expected_post_name, str(post))

    def test_groups_have_correct_object_name(self):
        group = PostsAppModelTest.group
        expected_group_name = group.title
        self.assertEqual(expected_group_name, str(group))

    def test_verbose_names_for_post(self):
        post = PostsAppModelTest.post
        field_verbose_names = {
            'text': 'Заголовок',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа'
        }
        for field, expected_value in field_verbose_names.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_value)

    def test_help_texts_for_post(self):
        post = PostsAppModelTest.post
        field_help_texts = {
            'text': 'Напишите сюда что-нибудь',
            'group': 'Выберите группу'
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected_value)

    def test_verbose_names_for_group(self):
        group = PostsAppModelTest.group
        field_verbose_names = {
            'title': 'Заголовок',
            'slug': 'Адрес страницы группы',
            'description': 'Описание'
        }
        for field, expected_value in field_verbose_names.items():
            with self.subTest(field=field):
                self.assertEqual(
                    group._meta.get_field(field).verbose_name, expected_value)

    def test_help_texts_for_group(self):
        group = PostsAppModelTest.group
        field_help_texts = {
            'title': 'Придумайте название группы',
            'slug': ('Укажите адрес для страницы группы. '
                     'Используйте только '
                     'латиницу, цифры, '
                     'дефисы и знаки подчёркивания'),
            'description': 'О чем эта группа?'
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    group._meta.get_field(field).help_text, expected_value)
