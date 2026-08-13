from django import template

register = template.Library()

@register.filter(name='subtract')
def subtract(value, arg):
    """Resta arg de value"""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0