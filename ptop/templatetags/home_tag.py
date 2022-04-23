from django import template
from datetime import datetime, timedelta
import numpy as np
import math

register = template.Library()

@register.filter(name="multiply")
def multiply(value, args):
    return value * args
    
@register.filter(name="divide")
def divide(value, args):
    return value / args

@register.filter(name="duration_hour")
def duration_hour(td):
    print(td)
    return (td.total_seconds()/3600.0)

@register.filter(name="weekday_jp")
def weekday_jp(value):
    return (value.strftime('%a'))

@register.filter(name="percent")
def percent(value, args):
    if math.isnan(value):
        return '-'
    elif math.isinf(value):
        return '-'
    else:
        return str(round(value*100.0, args))+'%'
#        return round(value*100.0, args)

@register.simple_tag
def url_replace(request, field, value):
    """GETパラメータを一部を置き換える"""

    url_dict = request.GET.copy()
    url_dict[field] = str(value)  # Django2.1の一部対策。通常はvalueだけでOK
    return url_dict.urlencode()


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)