# core/templatetags/user_extras.py
from django import template

register = template.Library()

@register.filter
def is_vendedor(user):
    return user.groups.filter(name='Vendedor').exists()