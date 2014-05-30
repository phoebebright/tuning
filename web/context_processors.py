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

    context['DEFAULT_DEADLINE_TIME'] = settings.DEFAULT_DEADLINE_TIME.replace(':','')
    context['USER_TIME_ZONE'] = settings.USER_TIME_ZONE
    context['CALENDAR_MIN_TIME'] = settings.CALENDAR_MIN_TIME
    context['CALENDAR_MAX_TIME'] = settings.CALENDAR_MAX_TIME

    #TODO: optimise these calls they are calling custmuser for every record
    #TODO: try specifying values requred

    if not request.user.is_anonymous():
    
        if request.user.is_superuser:
            context['CELERY_MONITOR_URL'] = settings.CELERY_MONITOR_URL
            context['RABBITMQ_MONITOR_URL'] = settings.RABBITMQ_MONITOR_URL
            
            
        if request.user.is_admin:

            context['num_requested'] = Booking.objects.requested().count()
            context['list_requested'] = Booking.objects.requested().select_related().order_by('deadline')
            context['num_current'] = Booking.objects.booked().count()
            context['list_current'] = Booking.objects.booked().select_related().order_by('deadline')
            context['num_to_complete'] = Booking.objects.to_complete().count()
            context['list_to_complete'] = Booking.objects.to_complete().select_related().order_by('deadline')
            context['num_complete'] = Booking.objects.completed().count()
            context['list_complete'] = Booking.objects.completed().select_related().order_by('deadline')

            # admins need a list of clients for the new bookings menu item
            context['CLIENTS'] = Client.objects.active()


        elif request.user.is_booker:
            context['num_requested'] = Booking.objects.ours(request.user.client).requested().count()
            context['list_requested'] = Booking.objects.ours(request.user.client).requested().select_related().order_by('deadline')
            context['num_current'] = Booking.objects.ours(request.user.client).booked().count()
            context['list_current'] = Booking.objects.ours(request.user.client).booked().select_related().order_by('deadline')
            context['num_to_complete'] = Booking.objects.ours(request.user.client).to_complete().count()
            context['list_to_complete'] = Booking.objects.ours(request.user.client).to_complete().select_related().order_by('deadline')
            context['num_complete'] = Booking.objects.ours(request.user.client).unpaid(request.user).count()
            context['list_complete'] = Booking.objects.ours(request.user.client).unpaid(request.user).select_related().order_by('deadline')

            context['CLIENTS'] = []


        elif request.user.is_tuner:
            context['num_requested'] = Booking.objects.requested().count()
            context['list_requested'] = Booking.objects.requested().select_related().order_by('deadline')
            context['num_current'] = Booking.objects.mine(request.user).booked().count()
            context['list_current'] = Booking.objects.mine(request.user).booked().select_related().order_by('deadline')
            context['num_to_complete'] = Booking.objects.mine(request.user).to_complete().count()
            context['list_to_complete'] = Booking.objects.mine(request.user).to_complete().select_related().order_by('deadline')
            context['num_complete'] = Booking.objects.mine(request.user).unpaid(request.user).count()
            context['list_complete'] = Booking.objects.mine(request.user).unpaid(request.user).select_related().order_by('deadline')

            context['CLIENTS'] = []



    return context

