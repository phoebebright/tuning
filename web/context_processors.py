from django.conf import settings

def add_stuff(request):

    from libs.faketime import now
    from datetime import timedelta

    context = {}


    context['DEBUG'] = settings.DEBUG
    context['NOW'] = now()
    context['TODAY'] = context['NOW'].date()
    context['YESTERDAY'] = context['TODAY'] - timedelta(days = 1)
    context['TOMORROW'] = context['TODAY'] + timedelta(days = 1)


    return context

