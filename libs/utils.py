from datetime import datetime, date, time

from django.conf import settings
from django.utils import timezone
import arrow

def is_list(arg):
    return (not hasattr(arg, "strip") and
            hasattr(arg, "__getitem__") or
            hasattr(arg, "__iter__"))


def make_time(dt, round_direction="start"):
    ''' convert a date to a datetime if not already a datetime
    second arguments tells whether time should be start or end of day
    make timezone aware if necessary
    '''

    #TODO: use arrow instead

    # ignore blanks
    if not dt:
        return None

    # if already a datetime, just make sure it is timezone aware
    if hasattr(dt, 'hour'):

        return add_tz(dt)

    else:
        # add time at start or end of day
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



def required(wrapping_functions,patterns_rslt):
    '''
    http://stackoverflow.com/questions/2307926/is-it-possible-to-decorate-include-in-django-urls-with-login-required
    Used to require 1..n decorators in any view returned by a url tree

    Usage:
      urlpatterns = required(func,patterns(...))
      urlpatterns = required((func,func,func),patterns(...))

    Note:
      Use functools.partial to pass keyword params to the required
      decorators. If you need to pass args you will have to write a
      wrapper function.

    Example:
      from functools import partial

      urlpatterns = required(
          partial(login_required,login_url='/accounts/login/'),
          patterns(...)
      )
    '''
    if not hasattr(wrapping_functions,'__iter__'):
        wrapping_functions = (wrapping_functions,)

    return [
        _wrap_instance__resolve(wrapping_functions,instance)
        for instance in patterns_rslt
    ]

def _wrap_instance__resolve(wrapping_functions,instance):
    if not hasattr(instance,'resolve'): return instance
    resolve = getattr(instance,'resolve')

    def _wrap_func_in_returned_resolver_match(*args,**kwargs):
        rslt = resolve(*args,**kwargs)

        if not hasattr(rslt,'func'):return rslt
        f = getattr(rslt,'func')

        for _f in reversed(wrapping_functions):
            # @decorate the function from inner to outter
            f = _f(f)

        setattr(rslt,'func',f)

        return rslt

    setattr(instance,'resolve',_wrap_func_in_returned_resolver_match)

    return instance