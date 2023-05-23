from django.db import models
from django.contrib.auth.models import User
from django.db.models import Sum
from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.core.cache import cache
from django.utils.translation import gettext as _
from django.utils.translation import pgettext_lazy


class Author(models.Model):
    user_author = models.OneToOneField(User, on_delete=models.CASCADE)
    user_rating = models.IntegerField(default=0)

    def update_rating(self):
        rating_posts_author = \
            Post.objects.filter(author_post=self).aggregate(Sum('rating_news')).get('rating_news__sum') * 3
        rating_comments_author = \
            Comment.objects.filter(user_comment=self.user_author).aggregate(Sum('rating_comment')).\
            get('rating_comment__sum')
        rating_comments_posts = \
            Comment.objects.filter(post_comment__author_post=self.id).aggregate(Sum('rating_comment')).\
            get('rating_comment__sum')

        self.user_rating = rating_posts_author + rating_comments_author + rating_comments_posts
        print(self.user_rating)
        self.save()

    def __str__(self):
        return self.user_author.username


class Category(models.Model):
    tehnika = 'TH'
    nauka = 'NA'
    sport = 'ST'
    spase = 'SP'

    TEMATIC = [
        (tehnika, 'ТЕХНИКА'),
        (nauka, 'НАУКА'),
        (sport, 'СПОРТ'),
        (spase, 'КОСМОС')
    ]
    tematic = models.CharField(max_length=2, choices=TEMATIC, unique=True)
    subscribers = models.ManyToManyField(User, blank=True, related_name='categories')
    name = models.CharField(max_length=100, help_text=_('category name'), default='')  # добавим переводящийся текст подсказку к полю

    def __str__(self):
        return self.get_tematic_display()


post = 'PO'
news = 'NE'
POST = [
    (post, 'ПОСТ'),
    (news, 'НОВОСТЬ')
]


class Post(models.Model):
    author_post = models.ForeignKey(Author, on_delete=models.CASCADE)
    post_news = models.CharField(max_length=2, choices=POST)
    date_in = models.DateTimeField(auto_now_add=True)
    category = models.ManyToManyField(Category, through='PostCategory')
    title = models.CharField(max_length=50)
    text = models.TextField()
    rating_news = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-date_in']

    def like_post(self):
        self.rating_news += 1
        self.save()

    def dislike_post(self):
        self.rating_news -= 1
        self.save()

    def preview(self):
        return self.text[0:124] + '...'

    def get_absolute_url(self):  # добавим абсолютный путь, чтобы после создания нас перебрасывало на страницу с постом
        return f'/news/{self.id}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # сначала вызываем метод родителя, чтобы объект сохранился
        cache.delete(f'post-{self.pk}')  # затем удаляем его из кэша, чтобы сбросить его


class PostCategory(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)


class Comment(models.Model):
    text_comment = models.TextField()
    data_time_comment = models.DateTimeField(auto_now_add=True)
    rating_comment = models.IntegerField(default=0)
    post_comment = models.ForeignKey(Post, on_delete=models.CASCADE)
    user_comment = models.ForeignKey(User, on_delete=models.CASCADE)

    def like_comment(self):
        self.rating_comment += 1
        self.save()

    def dislike_comment(self):
        self.rating_comment -= 1
        self.save()


class BaseRegisterForm(UserCreationForm):
    email = forms.EmailField(label="Email")
    first_name = forms.CharField(label="Имя")
    last_name = forms.CharField(label="Фамилия")

    class Meta:
        model = User
        fields = ("username",
                  "first_name",
                  "last_name",
                  "email",
                  "password1",
                  "password2", )


class MyModel(models.Model):
    name = models.CharField(max_length=100)
    kind = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='kinds',
        verbose_name=pgettext_lazy('help text for MyModel model', 'This is the help text'),
    )
