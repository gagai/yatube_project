from django.contrib import admin

from .models import Group, Post, Follow


class PostAdmin(admin.ModelAdmin):
    list_display = ('pk', 'group', 'text', 'pub_date', 'author',)
    search_fields = ('text',)
    list_filter = ('pub_date',)
    list_editable = ('group',)
    empty_value_display = '-пусто-'


admin.site.register(Post, PostAdmin)


class GroupAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug')
    search_fields = ('title', 'slug')
    empty_value_display = '-пусто-'


admin.site.register(Group)


class FollowAdmin(admin.ModelAdmin):
    list_display = ('user', 'author')
    search_fields = ('user', 'author')
    empty_value_display = '-пусто-'


admin.site.register(Follow)
