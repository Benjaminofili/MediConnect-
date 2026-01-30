from django import template

register = template.Library()

@register.filter
def sub(value, arg):
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        return value

@register.filter
def add(value, arg):
    try:
        return int(value) + int(arg)
    except (ValueError, TypeError):
        return value