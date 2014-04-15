from django.http import HttpResponse, HttpResponseRedirect

from functools import wraps

def can_book(permission):
    def decorator(func):
        def inner_decorator(request, *args, **kwargs):
            if request.user and request.user.is_authenticated():
                return  request.user.is_booker or request.user.is_admin


            else:
                return HttpResponseRedirect('/')

        return wraps(func)(inner_decorator)

    return decorator