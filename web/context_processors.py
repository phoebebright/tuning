from django.conf import settings
from web.models import Booking, Client

def add_stuff(request):

    from libs.faketime import now
    from datetime import timedelta

    context = {}


    context['DEBUG'] = settings.DEBUG
    context['DEFAULT_SLOT_TIME'] = settings.DEFAULT_SLOT_TIME
    context['API_URL'] = settings.API_URL
    context['MAX_BOOK_DAYS_IN_ADVANCE'] = settings.MAX_BOOK_DAYS_IN_ADVANCE
    context['MAX_DATE'] = now() + timedelta(days=settings.MAX_BOOK_DAYS_IN_ADVANCE)

    context['NOW'] = now()
    context['TODAY'] = context['NOW'].date()
    context['YESTERDAY'] = context['TODAY'] - timedelta(days = 1)
    context['TOMORROW'] = context['TODAY'] + timedelta(days = 1)

    #TODO: optimise these calls they are calling custmuser for every record
    #TODO: try specifying values requred
    context['num_requested'] = Booking.objects.requested().count()
    context['list_requested'] = Booking.objects.requested().select_related()[0:5]
    context['num_current'] = Booking.objects.current().count()
    context['list_current'] = Booking.objects.current().select_related()[0:5]
    context['num_to_complete'] = Booking.objects.to_complete().count()
    context['list_to_complete'] = Booking.objects.to_complete().select_related()[0:5]
    context['num_complete'] = Booking.objects.completed().count()
    context['list_complete'] = Booking.objects.completed().select_related()[0:5]

    # admins need a list of clients for the new bookings menu item
    context['CLIENTS'] = []
    if not request.user.is_anonymous():
        if request.user.is_admin:
            context['CLIENTS'] = Client.objects.active()



    return context

