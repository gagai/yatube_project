import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import PostForm, CommentForm
from ..models import Group, Post, Comment

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

        cls.group = Group.objects.create(title='test title',
                                         slug='test-slug',
                                         description='test description'
                                         )

        cls.post = Post.objects.create(text='test_text',
                                       author=cls.user,
                                       group=cls.group,
                                       )

        cls.username = cls.user.username
        cls.group_id = cls.group.id
        cls.post_id = cls.post.id

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
        posts_count = Post.objects.count()
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
        form_data = {
            'text': 'post_text',
            'group': self.group_id,
            'image': uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )

        # Получили последний пост из БД
        created_post = Post.objects.all().order_by('-id')[0]
        self.assertRedirects(response,
                             reverse('posts:profile',
                                     kwargs={'username': self.username}
                                     )
                             )
        self.assertEqual(Post.objects.count(), posts_count + 1)

        # Получили пост с id последнего созданного поста из БД и убедились,
        # что тот имеет те же данные, что использовались при создании поста
        self.assertTrue(Post.objects.filter(id=created_post.id,
                                            image='posts/small.gif'
                                            ).exists()
                        )

    def test_title_label(self):
        self.form = PostForm()
        title_labels = {
            'text': 'Текст поста',
            'group': 'Добавить группу'
        }

        for title, label in title_labels.items():
            value = self.form.fields[f'{title}'].label
            self.assertEquals(value, label)

    def test_title_help_text(self):
        self.form = PostForm()
        title_help_texts = {
            'text': 'Текст нового поста',
            'group': 'Группа, к которой будет относиться пост'
        }

        for title, help_text in title_help_texts.items():
            value = self.form.fields[f'{title}'].help_text
            self.assertEquals(value, help_text)

    def test_edit_post(self):
        old_post_id = self.post_id
        old_post_text = self.post.text
        old_post_group_id = self.post.group.id

        form_data = {
            'text': 'edited_post_text',
            'group': ''
        }
        response_post_edit = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post_id}),
            data=form_data,
            follow=True
        )
        new_post_id = response_post_edit.context.get('post').id
        new_post_text = response_post_edit.context.get('post').text
        new_post_group_id = response_post_edit.context.get('post').group

        self.assertEqual(old_post_id, new_post_id)
        self.assertNotEqual(old_post_text, new_post_text)
        self.assertIsNotNone(old_post_group_id)
        self.assertIsNone(new_post_group_id)


class CommentCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

        cls.group = Group.objects.create(title='test title',
                                         slug='test-slug',
                                         description='test description'
                                         )

        cls.post = Post.objects.create(text='test_text',
                                       author=cls.user,
                                       group=cls.group,
                                       )

        cls.username = cls.user.username
        cls.group_id = cls.group.id
        cls.post_id = cls.post.id

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_comment(self):
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Comment Test Text',
            'post': self.post,
            'author': self.user,
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment',
                    kwargs={'post_id': self.post_id}
                    ),
            data=form_data,
            follow=True,
        )
        comment_created_bool = Comment.objects.filter(**form_data).exists()
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertTrue(comment_created_bool)
        self.assertRedirects(response,
                             reverse('posts:post_detail',
                                     kwargs={'post_id': self.post_id}
                                     )
                             )

    def test_title_label(self):
        self.form = PostForm()
        title_labels = {
            'text': 'Текст поста',
        }

        for title, label in title_labels.items():
            value = self.form.fields[f'{title}'].label
            self.assertEquals(value, label)

    def test_title_help_text(self):
        self.form = CommentForm()
        title_help_texts = {
            'text': 'До 280 символов',
        }

        for title, help_text in title_help_texts.items():
            value = self.form.fields[f'{title}'].help_text
            self.assertEquals(value, help_text)
