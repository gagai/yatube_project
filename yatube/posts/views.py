from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from yatube.settings import POSTS_PER_PAGE

from .forms import PostForm, CommentForm
from .models import Group, Post, Comment, Follow
from .utils import get_page_obj

User = get_user_model()
ordering_post_default = '-pub_date'


@cache_page(20)
def index(request):
    post_list = Post.objects.all().order_by(ordering_post_default)
    page_obj = get_page_obj(request, post_list, POSTS_PER_PAGE)
    template = 'posts/index.html'
    title = 'Последние обновления на сайте'
    description = 'Это главная страница проекта Yatube'
    context = {
        'title': title,
        'description': description,
        'page_obj': page_obj
    }
    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    post_list = (Post.objects.
                 filter(group=group).
                 order_by(ordering_post_default)
                 )
    page_obj = get_page_obj(request, post_list, POSTS_PER_PAGE)
    context = {
        'group': group,
        'page_obj': page_obj
    }
    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    post_list = (Post.objects.
                 filter(author=author).
                 order_by(ordering_post_default)
                 )
    page_obj = get_page_obj(request, post_list, POSTS_PER_PAGE)
    posts_counter = Post.objects.filter(author=author).count()
    user = request.user

    following = []
    if user.is_authenticated:
        following = (
            Follow.objects.filter(user=request.user,
                                  author=author
                                  )
        )
    context = {
        'author': author,
        'user': user,
        'page_obj': page_obj,
        'posts_counter': posts_counter,
        'following': following
    }
    return render(request, template, context)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'
    post = get_object_or_404(Post, id=post_id)
    title = post.text[:30]
    posts_counter = Post.objects.filter(author=post.author).count()
    comments = Comment.objects.filter(post=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()

    context = {
        'post': post,
        'title': title,
        'posts_counter': posts_counter,
        'form': form,
        'comments': comments
    }
    return render(request, template, context)


@login_required
def post_create(request):
    template = 'posts/create_post.html'
    form = PostForm(request.POST or None,
                    files=request.FILES or None)
    context = {
        'form': form
    }
    if form.is_valid():
        form = form.save(commit=False)
        form.author = request.user
        form.save()
        return redirect('posts:profile', request.user.username)
    return render(request, template, context)


@login_required
def post_edit(request, post_id):
    is_edit = True
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post,
    )
    template = 'posts/create_post.html'
    context = {
        'form': form,
        'post': post,
        'is_edit': is_edit
    }
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    follower = request.user
    maps = Follow.objects.filter(user=follower)
    post_list = []
    for map in maps:
        post_list = Post.objects.filter(author=map.author)
    page_obj = get_page_obj(request, post_list, POSTS_PER_PAGE)
    title = 'Избранные авторы'
    description = ''
    if not page_obj:
        description = 'Так! А ну быстро подписался на кого-нибудь!'
    template = 'posts/follow.html'
    context = {
        'page_obj': page_obj,
        'title': title,
        'description': description,
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    follower = request.user
    author = get_object_or_404(User, username=username)
    if not (follower.username == username):
        if not(
            Follow.objects.filter(user=follower,
                                  author=author
                                  )
        ):
            Follow.objects.create(
                user=follower,
                author=get_object_or_404(User, username=username)
            )
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    follower = request.user
    author = get_object_or_404(User, username=username)
    follow_for_delete = get_object_or_404(Follow, user=follower, author=author)
    if not (follower.username == username):
        if (
            Follow.objects.filter(user=follower,
                                  author=author
                                  )
        ):
            follow_for_delete.delete()
    return redirect('posts:profile', username=username)