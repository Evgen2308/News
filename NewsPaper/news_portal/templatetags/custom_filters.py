from django import template

register = template.Library()

censor_list = ['редиска', 'проституция']


@register.filter()
def censor(value):
    for word in censor_list:
        value = value.replace(word[1:], '*' * len(word[1:]))
    return value