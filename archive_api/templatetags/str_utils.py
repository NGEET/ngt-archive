from django import template

register = template.Library()


@register.filter(name='split')
def split(value, arg):
    return value.rstrip(arg).lstrip(arg).split(arg)


@register.filter(name='breadcrumb_convert')
def breadcrumb_name(value, url):
    values = url.rstrip("/").lstrip("/").split("/")
    if len(values) > 2:
        return values[-1].title()
    else:
        return value

@register.filter(name='dict_key')
def dict_key(d, k):
    """Returns the given key from a dictionary."""
    return d[k]
