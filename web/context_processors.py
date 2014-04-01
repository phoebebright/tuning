from django.conf import settings
from web.models import Booking

def add_stuff(request):

    from libs.faketime import now
    from datetime import timedelta

    context = {}


    context['DEBUG'] = settings.DEBUG
    context['DEFAULT_SLOT_TIME'] = settings.DEFAULT_SLOT_TIME
    context['API_URL'] = settings.API_URL
    context['MAX_BOOK_DAYS_IN_ADVANCE'] = settings.MAX_BOOK_DAYS_IN_ADVANCE

    context['NOW'] = now()
    context['TODAY'] = context['NOW'].date()
    context['YESTERDAY'] = context['TODAY'] - timedelta(days = 1)
    context['TOMORROW'] = context['TODAY'] + timedelta(days = 1)

    context['requested'] = Booking.objects.requested()
    context['current'] = Booking.objects.current()
    context['complete'] = Booking.objects.complete()


    return context

