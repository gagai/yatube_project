from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Post(models.Model):
    text = models.TextField(verbose_name='Заголовок',
                            help_text='Напишите сюда что-нибудь'
                            )
    pub_date = models.DateTimeField(auto_now_add=True,
                                    verbose_name='Дата публикации'
                                    )
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='posts',
                               verbose_name='Автор'
                               )
    group = models.ForeignKey('Group',
                              on_delete=models.SET_NULL,
                              blank=True,
                              null=True,
                              related_name='posts',
                              verbose_name='Группа',
                              help_text='Выберите группу'
                              )

    image = models.ImageField(
        verbose_name='Картинка',
        upload_to='posts/',
        blank=True
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'

    def __str__(self) -> str:
        return self.text[:15]


class Group(models.Model):
    title = models.CharField(verbose_name='Заголовок',
                             help_text='Придумайте название группы',
                             max_length=200
                             )
    slug = models.SlugField(verbose_name='Адрес страницы группы',
                            help_text=('Укажите адрес для страницы группы. '
                                       'Используйте только '
                                       'латиницу, цифры, '
                                       'дефисы и знаки подчёркивания'),
                            unique=True)
    description = models.TextField(verbose_name='Описание',
                                   help_text='О чем эта группа?'
                                   )

    class Meta:
        ordering = ('title',)
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'

    def __str__(self) -> str:
        return self.title


class Comment(models.Model):
    post = models.ForeignKey(Post,
                             on_delete=models.SET_NULL,
                             null=True,
                             related_name='parent_post',
                             verbose_name='Пост комментария',
                             )
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='comment_author',
                               verbose_name='Автор комментария'
                               )
    created = models.DateTimeField(auto_now_add=True,
                                   verbose_name='Дата публикации'
                                   )
    text = models.TextField(verbose_name='Текст комментария',
                            help_text='Максимум 280 символов',
                            max_length=280
                            )

    class Meta:
        ordering = ('-created',)
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'


class Follow(models.Model):
    user = models.ForeignKey(User,
                             related_name='follower',
                             verbose_name='Подписчик',
                             on_delete=models.CASCADE,
                             )
    author = models.ForeignKey(User,
                               related_name='following',
                               verbose_name='Автор',
                               on_delete=models.CASCADE,)

    class Meta:
        ordering = ('user',)
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(fields=['user', 'author'],
                                    name='unique_follow'
                                    )
        ]
