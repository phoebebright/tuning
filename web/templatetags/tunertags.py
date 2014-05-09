from django import template
from django.utils.safestring import mark_safe

import json
from django.forms.models import model_to_dict
from decimal import Decimal
import datetime

register = template.Library()


def decimal_default(obj):

    if isinstance(obj, Decimal):
        return str(obj)

    if isinstance(obj, datetime.datetime):
        return 'new Date(%i,%i,%i,%i,%i,%i)' % (obj.year,
                                                      obj.month-1,
                                                      obj.day,
                                                      obj.hour,
                                                      obj.minute,
                                                      obj.second)
    if isinstance(obj, datetime.date):
        return 'new Date(%i,%i,%i)' % (obj.year,
                                         obj.month-1,
                                         obj.day)
    return obj




@register.filter(name='json')
def json_dumps(data):

    if type(data) is str:
        return ""

    #assume data is a model object
    #data = model_to_dict(data)

    return mark_safe(json.dumps(data, default=decimal_default))



