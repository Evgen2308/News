from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .filters import PostFilter
from .forms import PostForm
from .models import Post, Category, Author
from .tasks import send_email_task

from django.views.decorators.cache import cache_page
from django.core.cache import cache
from django.utils.translation import gettext as _

@cache_page(100)
def home(request):
    return render(request, 'home.html')


class PostsList(ListView):
    model = Post
    ordering = '-date_creation'
    template_name = 'posts.html'
    context_object_name = 'posts'
    paginate_by = 7

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['next_sale'] = None
        context['post_detail'] = Post
        return context


class PostDetail(DetailView):
    model = Post
    template_name = 'post.html'
    context_object_name = 'post'

    def get_object(self, *args, **kwargs):
        obj = cache.get(f'article-{self.kwargs["pk"]}', None)
        if not obj:
            obj = super().get_object(queryset=self.queryset)
            cache.set(f'article-{self.kwargs["pk"]}', obj)
        return obj



class PostSearch(ListView):
    model = Post
    template_name = 'post_search.html'
    context_object_name = 'posts'
    ordering = '-date_creation'
    paginate_by = 7

    def get_queryset(self):
        queryset = super().get_queryset()
        self.filterset = PostFilter(self.request.GET, queryset)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filterset'] = self.filterset
        context['next_sale'] = None
        return context


class PostCreate(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    form_class = PostForm
    model = Post
    template_name = 'post_create.html'
    permission_required = ('news.add_post',)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.get_type()
        return context

    def form_valid(self, form):
        post = form.save(commit=False)
        if self.request.method == 'POST':
            path_create = self.request.META['PATH_INFO']
            if path_create == '/news/create/':
                post.post_type = 'NW'
            elif path_create == '/news/articles/create/':
                post.post_type = 'AR'
            form.instance.author = self.request.user.author
        post.save()
        send_email_task.delay(post.pk)
        return super().form_valid(form)

    def get_type(self):
        path_type = self.request.META['PATH_INFO']
        if path_type == '/news/create/':
            return 'новость'
        elif path_type == '/news/articles/create/':
            return 'статью'


class PostUpdate(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    form_class = PostForm
    model = Post
    template_name = 'post_edit.html'
    permission_required = ('news.change_post',)

    def form_valid(self, form):
        post = form.save(commit=False)
        if self.request.method == 'POST':
            path_edit = self.request.META['PATH_INFO']
            if path_edit == f'/news/{post.pk}/edit/' and post.post_type != 'NW':
                return redirect(self.request.META.get('HTTP_REFERER'))
            elif path_edit == f'/news/articles/{post.pk}/edit/' and post.post_type != 'AR':
                return redirect(self.request.META.get('HTTP_REFERER'))
        post.save()
        return super().form_valid(form)


class PostDelete(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Post
    template_name = 'post_delete.html'
    success_url = reverse_lazy('post_list')
    permission_required = ('news.delete_post',)


class CategoryListView(ListView):
    model = Post
    template_name = 'category_list.html'
    context_object_name = 'category_posts_list'
    paginate_by = 10

    def get_queryset(self):
        self.post_category = get_object_or_404(Category, id=self.kwargs['pk'])
        queryset = Post.objects.filter(post_category=self.post_category).order_by('-date_creation')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_not_subscriber'] = self.request.user not in self.post_category.subscribers.all()
        context['is_subscriber'] = self.request.user in self.post_category.subscribers.all()
        context['category'] = self.post_category
        return context


@login_required
def subscribe(request, pk):
    user = request.user
    category = Category.objects.get(id=pk)
    category.subscribers.add(user)
    return redirect(f'/news/categories/{category.pk}')


@login_required
def unsubscribe(request, pk):
    user = request.user
    category = Category.objects.get(id=pk)
    category.subscribers.remove(user)
    return redirect(f'/news/categories/{category.pk}')


class AuthorsListView(ListView):
    model = Post
    template_name = 'authors_list.html'
    context_object_name = 'authors_post_list'
    paginate_by = 10

    def get_queryset(self):
        self.author = get_object_or_404(Author, id=self.kwargs['pk'])
        queryset = Post.objects.filter(author=self.author).order_by('-date_creation')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['author'] = self.author
        return context


class PostTypeListView(ListView):
    model = Post
    template_name = 'post_type.html'
    context_object_name = 'post_type_list'
    paginate_by = 10

    def get_queryset(self):
        queryset = Post.objects.filter(post_type=self.get_type()[0]).order_by('-date_creation')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['post_type'] = self.get_type()[1]
        return context

    def get_type(self):
        path_type = self.request.META['PATH_INFO']
        if path_type == '/news/type/NW':
            return 'NW', 'новостей'
        elif path_type == '/news/type/AR':
            return 'AR', 'статей'


class Index(View):
    def get(self, request):
        string = _('Hello world')

        return HttpResponse(string)