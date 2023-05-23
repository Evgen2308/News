from django.contrib import admin
from .models import Author, Category, Post, Comment
from modeltranslation.admin import TranslationAdmin
# импортируем модель амдинки (вспоминаем модуль про переопределение стандартных админ-инструментов)


# Register your models here.

# Регистрируем модели для перевода в админке

class CategoryAdmin(TranslationAdmin):
    model = Category


# class MyModelAdmin(TranslationAdmin):
#     model = MyModel


# class PostAdmin(admin.ModelAdmin):
#     list_display = [field.name for field in Post._meta.get_fields()] # генерируем список имен полей
#     list_display = ('title', 'category')


admin.site.register(Author)
admin.site.register(Category)
admin.site.register(Post)
admin.site.register(Comment)