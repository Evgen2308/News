from django import forms
# from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from .models import Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['post_title', 'post_text', 'post_category']
        labels = {
            'post_title': 'Заголовок',
            'post_text': 'Текст',
            'post_category': 'Категории',
        }

    def clean(self):
        cleaned_data = super().clean()
        post_title = cleaned_data.get('post_title')
        post_text = cleaned_data.get('post_text')
        if post_text is not None and post_text == post_title:
            raise ValidationError({
                'post_text': 'Текст статьи не должен совпадать с заголовком'
            })
        return cleaned_data