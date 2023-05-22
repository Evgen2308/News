from django.urls import path
from .views import PostsList, PostDetail, PostSearch, PostCreate, PostUpdate, PostDelete, CategoryListView, subscribe, \
    AuthorsListView, PostTypeListView, unsubscribe

from django.views.decorators.cache import cache_page

urlpatterns = [
    path('', cache_page(300)(PostsList.as_view()), name='post_list'),
    path('<int:pk>/', cache_page(300)(PostDetail.as_view()), name='post_detail'),
    path('search/', PostSearch.as_view(), name='post_search'),
    path('create/', cache_page(300)(PostCreate.as_view()), name='post_create'),
    path('<int:pk>/edit/', PostUpdate.as_view(), name='post_edit'),
    path('<int:pk>/delete/', PostDelete.as_view(), name='post_delete'),
    path('articles/create/', cache_page(300)(PostCreate.as_view()), name='articles_create'),
    path('articles/<int:pk>/edit/', PostUpdate.as_view(), name='articles_edit'),
    path('articles/<int:pk>/delete', PostDelete.as_view(), name='articles_delete'),
    path('categories/<int:pk>', CategoryListView.as_view(), name='category_list'),
    path('categories/<int:pk>/subscribe', subscribe, name='subscribe'),
    path('categories/<int:pk>/unsubscribe', unsubscribe, name='unsubscribe'),
    path('author/<int:pk>', AuthorsListView.as_view(), name='author_list'),
    path('type/<str:post_type>', PostTypeListView.as_view(), name='type_list'),
]