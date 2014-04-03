from datetime import datetime, date, time

from django.conf import settings
from django.utils import timezone

def is_list(arg):
    return (not hasattr(arg, "strip") and
            hasattr(arg, "__getitem__") or
            hasattr(arg, "__iter__"))


def make_time(dt, round_direction="start"):
    ''' convert a date to a datetime if not already a datetime
    second arguments tells whether time should be start or end of day
    make timezone aware if necessary
    '''
    if hasattr(dt, 'hour'):

        return dt

    else:
        if round_direction == "start":
            dt = datetime.combine(dt, time.min)
        else:
            dt = datetime.combine(dt, time.max)



    # make timezone aware if required
    dt =  add_tz(dt)

    return dt

def add_tz(value):
    """
    Makes a naive datetime.datetime in the timezone in settings
    """
    tz = timezone.get_current_timezone()
    if settings.USE_TZ:

        if timezone.is_naive(value):
            return timezone.make_aware(value, tz)


    else:
        if timezone.is_aware(value):
            return timezone.make_naive(value, tz)

    return value