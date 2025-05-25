from django import template

from django.forms import BaseForm

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def pluck(objects, attr):
    return [getattr(obj, attr) for obj in objects]

@register.filter
def contains(value_list, item):
    return item in value_list



register = template.Library()

@register.filter
def as_p(form):
    if isinstance(form, BaseForm):
        return form.as_p()
    return form