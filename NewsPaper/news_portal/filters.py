from django_filters import FilterSet, DateFilter, CharFilter, ModelChoiceFilter
from .models import Author
from django import forms
from django.utils.translation import gettext as _


class PostFilter(FilterSet):
    search_title = CharFilter(
        field_name='post_title',
        label='Заголовок',
        lookup_expr='icontains'
    )
    search_author = ModelChoiceFilter(
        empty_label='Все авторы',
        field_name='author',
        label='Автор',
        queryset=Author.objects.all()
    )

    post_date = DateFilter(
        field_name='date_creation',
        widget=forms.DateInput(attrs={'type': 'date'}),
        label=_('search by date starting from'),
        lookup_expr='date__gte'
    )