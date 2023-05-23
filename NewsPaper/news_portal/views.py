import pytz
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, UpdateView, DeleteView
from requests import request, Response
from datetime import datetime, timedelta

from django.http import HttpResponse
from django.views import View

from .models import Post, Category, BaseRegisterForm, Author, post, MyModel
from .forms import PostForm
from .filter import PostFilter
from django.contrib.auth.models import User, Group
from django.views.generic.edit import CreateView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import redirect, get_object_or_404, render
from django.contrib.auth.decorators import login_required

from .tasks import send_email_task
from django.core.cache import cache
from django.utils.translation import gettext as _
from django.utils import timezone
from django.utils.translation import activate, get_supported_language_variant, LANGUAGE_SESSION_KEY
from rest_framework import viewsets, permissions, status
from news_portal.serializers import AuthorSerializer, PostSerializer
from news_portal.models import Author, Post



@login_required
def upgrade_me(request):
    Author.objects.create(user_author=request.user)
    authors_group = Group.objects.get(name='authors')
    if not request.user.groups.filter(name='authors').exists():
        authors_group.user_set.add(request.user)
    return redirect('/news/')


class PostList(LoginRequiredMixin, ListView):
    model = Post
    ordering = ['-date_in']
    template_name = 'news.html'
    context_object_name = 'post_news'
    paginate_by = 5
    form_class = PostForm

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.order_by('-date_in')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = PostFilter(self.request.GET, queryset=self.get_queryset())
        context['categories'] = Category.objects.all()
        context['form'] = self.form_class()  # создаем экземпляр формы, чтобы передать в контекст
        context['is_not_author'] = not self.request.user.groups.filter(name='authors').exists()
        context['current_time'] = timezone.now()
        context['timezones'] = pytz.common_timezones

        return context

    def post(self, request):
        request.session['django_timezone'] = request.POST['timezone']
        return redirect('post_list')


class PostDetail(LoginRequiredMixin, DetailView):
    model = Post
    template_name = 'onenews.html'
    context_object_name = 'onenews'
    queryset = Post.objects.all()

    def get_object(self, *args, **kwargs):  # переопределяем метод получения объекта
        obj = cache.get(f'post-{self.kwargs["pk"]}', None)
        # кэш очень похож на словарь, и метод get действует так же. Он забирает значение по ключу, если его нет, то забирает None.
        # если объекта нет в кэше, то получаем его и записываем в кэш
        if not obj:
            obj = super().get_object(queryset=self.queryset)
            cache.set(f'post-{self.kwargs["pk"]}', obj)

        return obj


class PostCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):   # создание поста
    permission_required = 'news.add_post'
    template_name = 'post_add.html'
    form_class = PostForm
    model = post
    success_url = reverse_lazy('post_add')

    def form_valid(self, form):
        post = form.save(commit=False)
        post.save()
        send_email_task.delay(post.pk)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.form_class()
        context['current_time'] = timezone.now()
        context['timezones'] = pytz.common_timezones
        return context

    def post(self, request, *args, **kwargs):
        request.session['django_timezone'] = request.POST.get('timezone', 'UTC')
        return super().post(request, *args, **kwargs)


class PostUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):   # редактирование поста
    permission_required = 'news.change_post'
    template_name = 'post_edit.html'
    form_class = PostForm

    # метод get_object мы используем вместо queryset, чтобы получить информацию об объекте редактирования
    def get_object(self, **kwargs):
        id = self.kwargs.get('pk')
        return Post.objects.get(pk=id)

    def post(self, request, **kwargs):
        request.session['django_timezone'] = request.POST['timezone']
        return redirect('post_edit')

# дженерик для удаления поста

class PostDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    permission_required = 'news.delete_post'
    model = Post
    template_name = 'post_delete.html'
    queryset = Post.objects.all()
    success_url = '/news/'
    context_object_name = 'post_delete'


class PostSearch(ListView):   #поиск поста
    model = Post
    template_name = 'post_search.html'
    context_object_name = 'post_news'
    paginate_by = 5

    def get_queryset(self):  # получаем обычный запрос
        queryset = super().get_queryset()  # используем наш класс фильтрации
        self.filterset = PostFilter(self.request.GET, queryset)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filterset'] = self.filterset
        context['current_time'] = timezone.now()
        context['timezones'] = pytz.common_timezones
        return context

    def post(self, request):
        request.session['django_timezone'] = request.POST['timezone']
        return redirect('post_search')


class BaseRegisterView(CreateView):
    model = User
    form_class = BaseRegisterForm
    success_url = '/'


class CategoryListView(ListView):
    model = Post
    template_name = 'category_list.html'
    context_object_name = 'category_news_list'

    def get_queryset(self):
        self.category = get_object_or_404(Category, id=self.kwargs['pk'])
        queryset = Post.objects.filter(category=self.category).order_by('-date_in')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_not_subscriber'] = self.request.user not in self.category.subscribers.all()
        context['category'] = self.category
        return context


@login_required
def subscribe(request, pk):
    user = request.user
    category = Category.objects.get(id=pk)
    category.subscribers.add(user)
    message = _('you have subscribed to the category: ')
    return render(request, 'subscribe.html', {'category': category, 'message': message})


@login_required
def unsubscribe(request, pk):
    user = request.user
    category = Category.objects.get(id=pk)
    category.subscribers.remove(user)
    message = _('unsubscribe from a category: ')
    return render(request, 'subscribe.html', {'category': category, 'message': message})


class AuthorlViewset(viewsets.ModelViewSet):
   queryset = Author.objects.all()
   serializer_class = AuthorSerializer

   def list(self, request, format=None):
       return Response([])


class PostViewset(viewsets.ModelViewSet):
   queryset = Post.objects.all().filter(is_active=True)
   serializer_class = PostSerializer

   def destroy(self, request, pk, format=None):
       instance = self.get_object()
       instance.is_active = False
       instance.save()
       return Response(status=status.HTTP_204_NO_CONTENT)
